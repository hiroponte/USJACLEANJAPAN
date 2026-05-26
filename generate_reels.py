# -*- coding: utf-8 -*-
"""
generate_reels.py  v8
修正:
  - 画像をcontainモードで表示（全体が見える状態でスタート）→ KB10%ズームで端が切れない
  - フォントweight 800→900（Black）でより太く
  - ドロップシャドウ追加（アウトラインに加えて）
  - フックテキスト・メインテキストのサイズ強化
"""

import os, sys, wave
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ASSETS    = Path(r"C:\Users\lsbre\Desktop\Antigravity\USJACLEAN HP\assets")
OUTPUT    = Path(r"C:\Users\lsbre\Desktop\Antigravity\USJACLEAN HP\reels")
FONT_PATH = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"

W, H   = 1080, 1920
FPS    = 30
FADE_F = int(FPS * 0.35)

IMG_ZONE_H   = int(H * 0.55)
TEXT_ZONE_H  = H - IMG_ZONE_H
ACCENT_COLOR = (0, 190, 165)
KB_ZOOM_MAX  = 1.10   # containモードからズームする倍率上限

HOOK_SEC    = 1.5    # 冒頭テキスト表示秒数
REVEAL_SEC  = 0.7    # 画像フェードイン秒数

OUTPUT.mkdir(exist_ok=True)

# ──────────────────────────────────────────────
# BGM（Karplus-Strong 弦合成）
# ──────────────────────────────────────────────
SR = 44100

def _freq(n):
    t={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
    sh='#' in n; c=n[0]; o=int(n[-1])
    return 440.*(2**((t[c]+(1 if sh else 0)+(o-4)*12)/12.))

def _ks(freq, dur, brightness=0.9):
    ns=int(SR*dur); dl=max(2,int(SR/freq))
    rng=np.random.default_rng(int(freq*1000)%(2**31))
    buf=rng.standard_normal(dl).astype(np.float64)
    out=np.empty(ns,dtype=np.float64); b=buf.copy()
    for i in range(ns):
        out[i]=b[0]; nv=brightness*.5*(b[0]+b[1])
        b=np.roll(b,-1); b[-1]=nv
    el=min(ns,int(SR*1.8))
    out[:el]*=np.exp(-3.5*np.linspace(0,1,el))
    if ns>el: out[el:]=0.
    return out

def _pad(notes,dur,vol=0.13):
    n=int(SR*dur); out=np.zeros(n,dtype=np.float64)
    an,rn=int(SR*.45),int(SR*.6); sn=max(0,n-an-rn)
    env=np.concatenate([np.linspace(0,1,an),np.ones(sn),np.linspace(1,0,rn)])[:n]
    for note in notes:
        f=_freq(note); t=np.linspace(0,dur,n,endpoint=False)
        out+=(0.6*np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t)+0.1*np.sin(6*np.pi*f*t))*env
    return out*(vol/max(len(notes),1))

def _bass(note,dur,vol=0.26):
    f=_freq(note); n=int(SR*dur); t=np.linspace(0,dur,n,endpoint=False)
    w=np.sin(2*np.pi*f*t)+0.4*np.sin(4*np.pi*f*t)
    an,rn=int(SR*.04),int(SR*.35); sn=max(0,n-an-rn)
    env=np.concatenate([np.linspace(0,1,an),np.ones(sn),np.linspace(1,0,rn)])[:n]
    return w*env*vol

def _kick(dur=.25):
    n=int(SR*dur); t=np.linspace(0,dur,n,endpoint=False)
    return np.sin(2*np.pi*np.cumsum(80*np.exp(-18*t))/SR)*np.exp(-14*t)*.38

def _hh(dur=.04):
    n=int(SR*dur); t=np.linspace(0,dur,n,endpoint=False)
    return np.random.default_rng(7).standard_normal(n)*np.exp(-65*t)*.055

def _place(buf,sig,ps):
    s=int(ps*SR); e=min(s+len(sig),len(buf)); buf[s:e]+=sig[:e-s]

def generate_bgm(total_sec):
    # ウェルネス・健康器具向け: BPM65、ゆったりピアノアンビエント、ドラムなし
    buf=np.zeros(int(SR*total_sec),dtype=np.float64)
    beat=60./65; bar=beat*4; step=beat  # 4分音符で1音（ゆっくり）
    chords=[
        (['C4','E4','G4'], ['C3','E3','G3'], 'C2'),
        (['A3','C4','E4'], ['A2','C3','E3'], 'A2'),
        (['F3','A3','C4'], ['F2','A2','C3'], 'F2'),
        (['G3','B3','D4'], ['G2','B2','D3'], 'G2'),
    ]
    t=0.; ci=0
    while t<total_sec-bar:
        arps,pads,bass_n=chords[ci%len(chords)]
        # 柔らかいパッド（主役）
        _place(buf,_pad(pads,min(bar+.6,total_sec-t),vol=0.10),t)
        # 控えめなベース
        _place(buf,_bass(bass_n,beat*2.5,vol=0.13),t)
        # ゆっくりアルペジオ: 3音のみ、各音が長く響く
        for i,note in enumerate(arps):
            _place(buf,_ks(_freq(note),step*2.2,brightness=0.82)*.42,t+i*step)
        t+=bar; ci+=1
    # 広がりのあるリバーブ（深め）
    for i in range(1,5):
        d=int(.09*i*SR)
        if d<len(buf): buf[d:]+=buf[:-d]*(.28**i)
    fi,fo=int(SR*1.2),int(SR*2.2)
    buf[:fi]*=np.linspace(0,1,fi); buf[-fo:]*=np.linspace(1,0,fo)
    pk=np.max(np.abs(buf))
    return (buf/pk*.72).astype(np.float32) if pk>0 else buf.astype(np.float32)

def save_wav(audio,path):
    with wave.open(path,'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio*32767).astype(np.int16).tobytes())

# ──────────────────────────────────────────────
# フォント
# ──────────────────────────────────────────────
OFFICIAL_VIDEO = str(ASSETS / "vitality_swing_official.mp4")

def load_font(size, bold=True):
    try:
        f=ImageFont.truetype(FONT_PATH,size)
        if bold:
            try: f.set_variation_by_axes({'wght':900})
            except: pass
        return f
    except: return ImageFont.load_default()

def fit_font(draw, text, max_width, start_size, bold=True):
    """テキストがmax_widthに収まるまでフォントサイズを自動縮小"""
    size = start_size
    while size >= 36:
        fnt = load_font(size, bold)
        bb = draw.textbbox((0,0), text, font=fnt)
        if bb[2] - bb[0] <= max_width:
            return fnt, size
        size -= 4
    return load_font(36, bold), 36

# ──────────────────────────────────────────────
# フレーム生成
# ──────────────────────────────────────────────
def make_contain_zoom_frame(img, t_ratio):
    """
    containモード: 画像全体が見える状態でスタートし、KB_ZOOM_MAX倍までゆっくりズームイン。
    端が切れないので商品テキストも安全。背景は暗色で余白を埋める。
    """
    iw, ih = img.size
    # fitスケール: ゾーン内に全体が収まる最大倍率
    scale = min(W / iw, IMG_ZONE_H / ih)
    fw = int(iw * scale)
    fh = int(ih * scale)

    # KB: t=0→1.0倍(全体表示), t=1→KB_ZOOM_MAX倍(ズームイン)
    zoom = 1.0 + (KB_ZOOM_MAX - 1.0) * t_ratio
    sw = int(fw * zoom)
    sh = int(fh * zoom)
    scaled = img.resize((sw, sh), Image.LANCZOS)

    # ゾーンキャンバス（暗色背景）
    zone = Image.new("RGB", (W, IMG_ZONE_H), (8, 8, 14))

    # スケール済み画像の中央部分をキャンバスに配置
    cx = max(0, (sw - W) // 2)
    cy = max(0, (sh - IMG_ZONE_H) // 2)
    crop = scaled.crop((cx, cy, cx + min(sw, W), cy + min(sh, IMG_ZONE_H)))
    px = max(0, (W - crop.width) // 2)
    py = max(0, (IMG_ZONE_H - crop.height) // 2)
    zone.paste(crop, (px, py))
    return zone

def render_text_panel(main_lines, sub_text):
    panel=Image.new("RGB",(W,TEXT_ZONE_H),(10,10,16))
    draw=ImageDraw.Draw(panel)
    draw.rectangle([(0,0),(W,7)],fill=ACCENT_COLOR)
    ml=max(len(l) for l in main_lines)
    msz=92 if ml<=9 else 78 if ml<=13 else 66
    MAX_TW = W - 40  # 左右20pxずつ余白

    def dc(text, font, color, yp):
        bb=draw.textbbox((0,0),text,font=font); tw=bb[2]-bb[0]; x=max(20,(W-tw)//2)
        for dx,dy in [(-3,-3),(3,-3),(-3,3),(3,3),(-4,0),(4,0),(0,-4),(0,4)]:
            draw.text((x+dx,yp+dy),text,font=font,fill=(0,0,0))
        draw.text((x,yp),text,font=font,fill=color)

    # メイン行: 最も長い行に合わせてフォントサイズ確定
    worst = max(main_lines, key=len)
    fm, msz = fit_font(draw, worst, MAX_TW, msz)
    fs=load_font(54,bold=False); fc=load_font(50,bold=True)
    lh=msz+22
    tot=len(main_lines)*lh+((54+14) if sub_text else 0)+50+14+28*2
    y=max(30,(TEXT_ZONE_H-tot)//2)

    for line in main_lines:
        dc(line,fm,(255,255,255),y); y+=lh
    if sub_text:
        y+=28
        fs2, _ = fit_font(draw, sub_text, MAX_TW, 54, bold=False)
        dc(sub_text,fs2,(155,210,200),y); y+=54+14
    y+=28; dc("▶  プロフィールリンクから",fc,ACCENT_COLOR,y)
    return panel

def make_hook_frame(hook_lines):
    """冒頭フック: 全画面黒背景に大きいテキストのみ"""
    canvas=Image.new("RGB",(W,H),(8,8,14))
    draw=ImageDraw.Draw(canvas)
    draw.rectangle([(0,0),(W,8)],fill=ACCENT_COLOR)
    draw.rectangle([(0,H-8),(W,H)],fill=ACCENT_COLOR)

    MAX_TW = W - 60
    ml=max(len(l) for l in hook_lines)
    start_sz=112 if ml<=8 else 92 if ml<=12 else 78
    # 全行を収めるサイズを確定
    worst = max(hook_lines, key=len)
    fnt, sz = fit_font(draw, worst, MAX_TW, start_sz)
    lh=sz+30
    tot=len(hook_lines)*lh
    y=(H-tot)//2-40
    for line in hook_lines:
        bb=draw.textbbox((0,0),line,font=fnt); tw=bb[2]-bb[0]; x=max(30,(W-tw)//2)
        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4),(-5,0),(5,0),(0,-5),(0,5)]:
            draw.text((x+dx,y+dy),line,font=fnt,fill=(0,0,0))
        draw.text((x,y),line,font=fnt,fill=(255,255,255))
        y+=lh
    return np.array(canvas)

def make_video_slide_frames(video_path, start_sec, main_lines, sub_text, duration):
    """公式動画クリップからスライドフレームを生成（静止画の代わりに実映像を使用）"""
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(str(video_path)).subclip(start_sec, min(start_sec + duration, VideoFileClip(str(video_path)).duration))
    txt = np.array(render_text_panel(main_lines, sub_text))
    tf = int(duration * FPS)
    frames = []
    vid_dur = clip.duration
    for f in range(tf):
        t = min(f / FPS, vid_dur - 0.01)
        frame_arr = clip.get_frame(t)  # H×W×3 numpy array
        img = Image.fromarray(frame_arr.astype(np.uint8))
        tr = f / max(tf - 1, 1)
        zone = make_contain_zoom_frame(img, tr)
        za = np.array(zone, dtype=np.float32)
        grad = np.linspace(0, .25, IMG_ZONE_H)[:, np.newaxis, np.newaxis]
        za = np.clip(za * (1 - grad * .50), 0, 255).astype(np.uint8)
        frame = np.concatenate([za, txt], axis=0)
        frames.append(frame)
    clip.close()
    return frames

def make_slide_frames(img_path, main_lines, sub_text, duration):
    """通常スライドフレーム（フック後のスライドに使用）"""
    img=Image.open(img_path).convert("RGB")
    txt=np.array(render_text_panel(main_lines,sub_text))
    tf=int(duration*FPS); ts=int(FPS*.28); te=int(FPS*.72)
    frames=[]
    for f in range(tf):
        tr=f/max(tf-1,1)
        z=make_contain_zoom_frame(img, tr)
        za=np.array(z,dtype=np.float32)

        # 下端のみごく薄く暗化（テキストパネルとの境界を馴染ませる）
        grad=np.linspace(0,.25,IMG_ZONE_H)[:,np.newaxis,np.newaxis]
        za=np.clip(za*(1-grad*.50),0,255).astype(np.uint8)

        frame=np.concatenate([za,txt],axis=0)
        alpha=0. if f<ts else (f-ts)/(te-ts) if f<te else 1.
        if alpha<1.:
            frame[IMG_ZONE_H:]=(txt*alpha).astype(np.uint8)
        frames.append(frame)
    return frames

def make_first_slide_frames(img_path, hook_lines, main_lines, sub_text, slide_dur):
    """
    最初のスライド専用:
      [0, HOOK_SEC]    : フックテキスト全画面
      [HOOK_SEC, +REVEAL_SEC]: 通常レイアウトへクロスフェード
      [HOOK_SEC+REVEAL_SEC, end]: 通常表示
    """
    hook_f   = int(HOOK_SEC * FPS)
    reveal_f = int(REVEAL_SEC * FPS)
    normal_dur = slide_dur  # 通常スライド部の長さ
    normal_frames = make_slide_frames(img_path, main_lines, sub_text, normal_dur)

    hook_arr = make_hook_frame(hook_lines)
    frames = []

    # フックフェーズ（テキスト表示・わずかに揺れる）
    for f in range(hook_f):
        frames.append(hook_arr.copy())

    # リビールフェーズ（クロスフェード）
    for f in range(reveal_f):
        t = f / reveal_f
        norm = normal_frames[min(f, len(normal_frames)-1)].astype(np.float32)
        blended = (hook_arr.astype(np.float32)*(1-t) + norm*t).astype(np.uint8)
        frames.append(blended)

    # 通常フェーズ
    frames.extend(normal_frames[reveal_f:])
    return frames

def add_fade(a,b):
    out=list(a[:-FADE_F])
    for i in range(FADE_F):
        t=i/FADE_F
        out.append((a[-FADE_F+i].astype(np.float32)*(1-t)+b[i].astype(np.float32)*t).astype(np.uint8))
    out.extend(b[FADE_F:])
    return out

# ──────────────────────────────────────────────
# Reels定義
# hook: 冒頭1.5秒に全画面で表示するフックテキスト
# ──────────────────────────────────────────────
REELS = [
    {
        "filename": "reel_01_parent.mp4",
        "title": "Reels①「親への罪悪感」型",
        "video_start": 0.0,
        "hook": ["実家の親、", "腰が辛そうで…"],
        "slides": [
            ("product_vitality_swing.jpg", ["実家の親、最近", "腰が辛そうで…"],        "",                    3.5),
            ("vs_usage.jpg",               ["足を乗せるだけ。", "寝たままでOK。"],       "15分タイマー付き・静音設計",  3.5),
            ("vs_credentials.jpg",         ["理学療法士監修。", "高齢者にも安心。"],     "整形外科臨床経験10年以上",    4.0),
            ("vs_lifestyle.jpg",           ["詳しくは", "プロフィールから →"],           "Daiwa Felicity 公式",        4.0),
        ],
    },
    {
        "filename": "reel_02_secret.mp4",
        "title": "Reels②「知ってる人だけ得してる」型",
        "video_start": 3.0,
        "hook": ["全米20万台売れてるのに", "日本でほぼ知られてない"],
        "slides": [
            ("product_vitality_swing.jpg", ["全米20万台売れてるのに", "日本でほぼ知られてない"], "健康器具がある",          4.0),
            ("vs_credentials.jpg",         ["★4.4  /  2,600件", "ウォルマート採用"],           "理学療法士監修・全米NO.1", 3.5),
            ("vs_benefits.jpg",            ["腰・むくみ・疲労を", "寝ながら15分でリセット"],    "自動タイマー・静音設計",   3.5),
            ("vs_lifestyle.jpg",           ["知ってる人だけ", "使ってる段階。"],               "▶ プロフィールリンクから", 4.0),
        ],
    },
    {
        "filename": "reel_03_solution.mp4",
        "title": "Reels③「問題解決」型",
        "video_start": 6.0,
        "hook": ["腰が重くて", "眠れない夜、ありませんか？"],
        "slides": [
            ("vs_lifestyle.jpg",           ["腰が重くて", "眠れない夜の解決策"],          "3ステップで完結",              3.5),
            ("vs_usage.jpg",               ["STEP 1  横になる", "STEP 2  足首を乗せる"],  "STEP 3  スイッチON",           4.0),
            ("vs_benefits.jpg",            ["あとは器具が", "15分やってくれる"],          "タイマーOFF・静音・寝たままOK", 3.5),
            ("product_vitality_swing.jpg", ["全米20万台が", "証明した金魚運動"],          "▶ プロフィールリンクから",     4.0),
        ],
    },
    {
        "filename": "reel_04_education.mp4",
        "title": "Reels④「なぜ腰痛が起きるのか」教育型",
        "video_start": 9.0,
        "hook": ["腰痛の本当の原因、", "知ってますか？"],
        "slides": [
            ("vs_lifestyle.jpg",           ["腰が痛い原因は", "血流の低下"],             "座りっぱなしで足首が固まる",     4.0),
            ("vs_wave.jpg",                ["足首を動かすと", "全身の血流が変わる"],      "金魚運動＝自然の血流ポンプ",     4.0),
            ("vs_credentials.jpg",         ["理学療法士が", "これを選んだ理由"],          "整形外科臨床10年以上",           4.0),
            ("product_vitality_swing.jpg", ["足を乗せるだけ", "15分で動かしてくれる"],   "▶ プロフィールリンクから",      3.5),
        ],
    },
    {
        "filename": "reel_05_empathy.mp4",
        "title": "Reels⑤「デスクワーク女性の夜」共感型",
        "video_start": 12.0,
        "hook": ["座り仕事のあと", "腰がズーンと重い方へ"],
        "slides": [
            ("vs_lifestyle.jpg",           ["仕事終わり、", "腰がズーンと重い"],         "デスクワーク8時間の代償",        3.5),
            ("vs_usage.jpg",               ["帰宅後すぐ横になって", "足首を乗せるだけ"], "動かなくていい。動いてくれる。", 4.0),
            ("vs_benefits.jpg",            ["15分後には", "腰の重さがリセット"],         "自動タイマーOFF・静音設計",      4.0),
            ("product_vitality_swing.jpg", ["明日のために", "今夜15分だけ"],             "▶ プロフィールリンクから",      4.0),
        ],
    },
    {
        "filename": "reel_06_steps.mp4",
        "title": "Reels⑥「3ステップで完結」操作型",
        "video_start": 15.0,
        "hook": ["STEP1 横になる", "STEP2 乗せる  STEP3 押す"],
        "slides": [
            ("vs_lifestyle.jpg",           ["腰ケアって", "難しいと思ってませんか？"],   "実は3秒で始められます",          3.5),
            ("vs_usage.jpg",               ["STEP 1  横になる", "STEP 2  足首を乗せる"], "STEP 3  スイッチを押すだけ",     4.0),
            ("vs_wave.jpg",                ["あとは自動で", "ゆらゆら揺らしてくれる"],   "15分後に自動タイマーOFF",        4.0),
            ("product_vitality_swing.jpg", ["難しいことは", "何もない"],                 "▶ プロフィールリンクから",      4.0),
        ],
    },
    {
        "filename": "reel_07_gift.mp4",
        "title": "Reels⑦「親へのプレゼント」ギフト型",
        "video_start": 18.0,
        "hook": ["親へのプレゼント、", "何にするか迷ってませんか？"],
        "slides": [
            ("product_vitality_swing_box.jpg", ["実家の親への", "プレゼントに迷ったら"],    "これ1択でした",                  3.5),
            ("vs_usage.jpg",                   ["立てなくても", "運動経験ゼロでも使える"],  "足首を乗せるだけ",               4.0),
            ("vs_credentials.jpg",             ["理学療法士が", "高齢者にも安心と推薦"],    "整形外科10年の先生の言葉",       4.0),
            ("vs_lifestyle.jpg",               ["喜ばれる理由が", "ある器具です"],          "▶ プロフィールリンクから",      4.0),
        ],
    },
    {
        "filename": "reel_08_authority.mp4",
        "title": "Reels⑧「整形外科10年の先生が選んだ」権威型",
        "video_start": 20.0,
        "hook": ["整形外科10年の先生が", "自宅で使う器具があります"],
        "slides": [
            ("vs_credentials.jpg",         ["整形外科10年以上の", "理学療法士が監修"],    "なぜこの器具を選んだか",         4.0),
            ("vs_wave.jpg",                ["金魚運動は", "足首の自然な揺れを再現"],      "関節・筋肉への負荷がゼロ",       3.5),
            ("vs_benefits.jpg",            ["腰・むくみ・疲労を", "安全にアプローチ"],    "高齢者・術後の方にも安心",       4.0),
            ("product_vitality_swing.jpg", ["専門家が選んだ", "理由がわかる器具"],        "▶ プロフィールリンクから",      4.0),
        ],
    },
    {
        "filename": "reel_09_reviews.mp4",
        "title": "Reels⑨「2,600人が★4.4をつけた器具」社会的証明型",
        "video_start": 22.5,
        "hook": ["2,600人が使って", "★4.4をつけた器具"],
        "slides": [
            ("vs_credentials.jpg",         ["★4.4  /  2,600件", "Amazonレビュー"],       "ウォルマート採用・全米NO.1",     4.0),
            ("vs_benefits.jpg",            ["「腰が軽くなった」", "「むくみがとれた」"],  "「毎晩使っています」",           4.0),
            ("vs_usage.jpg",               ["使い方はシンプル", "足首を乗せて15分"],      "それだけで2,600件の声",          3.5),
            ("product_vitality_swing.jpg", ["2,600件の声が", "証明しています"],           "▶ プロフィールリンクから",      4.0),
        ],
    },
]

def make_reel(reel):
    print(f"\n=== {reel['title']} ===")
    out_path = OUTPUT / reel["filename"]

    # 1枚目: フック付き（公式動画 or 静止画）
    img0, ml0, st0, dur0 = reel["slides"][0]
    vid_start = reel.get("video_start", None)
    if vid_start is not None and Path(OFFICIAL_VIDEO).exists():
        print(f"  スライド1: 公式動画 t={vid_start}s ({dur0}s)")
        first_static = make_video_slide_frames(OFFICIAL_VIDEO, vid_start, ml0, st0, dur0)
    else:
        first_static = make_slide_frames(ASSETS/img0, ml0, st0, dur0)

    hook_arr = make_hook_frame(reel["hook"])
    hook_f   = int(HOOK_SEC * FPS)
    reveal_f = int(REVEAL_SEC * FPS)
    frames   = [hook_arr.copy()] * hook_f
    for f in range(reveal_f):
        t = f / reveal_f
        norm = first_static[min(f, len(first_static)-1)].astype(np.float32)
        frames.append((hook_arr.astype(np.float32)*(1-t) + norm*t).astype(np.uint8))
    frames.extend(first_static[reveal_f:])

    slide_lists = [frames]
    for img, ml, st, dur in reel["slides"][1:]:
        print(f"  スライド: {img} ({dur}s)")
        slide_lists.append(make_slide_frames(ASSETS/img, ml, st, dur))

    all_frames = slide_lists[0]
    for nxt in slide_lists[1:]:
        all_frames = add_fade(all_frames, nxt)


    total_sec = len(all_frames) / FPS
    print(f"  合計: {len(all_frames)}フレーム ({total_sec:.1f}s)  BGM生成中...")

    bgm = generate_bgm(total_sec)
    wav = str(out_path.with_suffix(".wav"))
    save_wav(bgm, wav)

    print(f"  書き出し中: {out_path.name} ...")
    from moviepy.editor import ImageSequenceClip, AudioFileClip
    clip  = ImageSequenceClip(list(np.stack(all_frames,axis=0)), fps=FPS)
    audio = AudioFileClip(wav).subclip(0, total_sec)
    clip  = clip.set_audio(audio)
    clip.write_videofile(str(out_path),codec="libx264",audio_codec="aac",
                         preset="medium",ffmpeg_params=["-crf","20","-pix_fmt","yuv420p"],
                         logger=None)
    audio.close(); os.remove(wav)
    print(f"  ✅ {out_path.name}")

def main():
    print("===== Reels 動画生成 v8 =====")
    if Path(OFFICIAL_VIDEO).exists():
        print("  ✅ 公式動画検出済み: 第1スライドに実映像を使用")
    else:
        print("  ⚠️  公式動画なし: 静止画で代替")
    for reel in REELS:
        make_reel(reel)
    print(f"\n===== 全3本 完成 =====\n{OUTPUT}")

if __name__ == "__main__":
    main()
