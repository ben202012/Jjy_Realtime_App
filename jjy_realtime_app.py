import streamlit as st
import numpy as np
import sounddevice as sd
import datetime, time

# Streamlit のページ設定とタイトル
st.set_page_config(page_title="JJYリアルタイム時刻合わせ", layout="centered")
st.title("JJYリアルタイム時刻合わせ")

# 指定した桁数の整数を BCD (Binary-Coded Decimal) に変換する関数
def to_bcd(value, digits):
    bcd = []
    for d in reversed(range(digits)):
        digit = (value // (10 ** d)) % 10  # 桁ごとの値を取り出す
        for i in [1, 2, 4, 8]:  # BCD: 4bitで表現（1, 2, 4, 8 の順）
            bcd.append((digit >> (i.bit_length() - 1)) & 1)  # 各bitを右シフトで抽出
    return bcd

# 現在の日時から60秒分のJJYビット列を生成する関数
def make_jjy_bits(dt):
    bits = ['0'] * 60  # 初期化（全て0）

    # マーカービット（毎10秒ごと + 最後）を'M'として設定
    for marker in [0, 9, 19, 29, 39, 49, 59]:
        bits[marker] = 'M'

    year = dt.year % 100
    bits[1:9] = list(map(str, to_bcd(year, 2)))  # 年（下2桁）
    bits[10:15] = list(map(str, to_bcd(dt.month, 2)[:5]))  # 月（5bit）
    bits[20:26] = list(map(str, to_bcd(dt.day, 2)[:6]))  # 日（6bit）

    weekday = (dt.weekday() + 1) % 7  # 曜日（0:日〜6:土）
    for i in range(3):
        bits[45 + i] = str((weekday >> i) & 1)

    bits[30:36] = list(map(str, to_bcd(dt.hour, 2)[:6]))  # 時（6bit）
    bits[40:47] = list(map(str, to_bcd(dt.minute, 2)[:7]))  # 分（7bit）

    return bits

# JJYビット列を音声で模擬的に再生する関数
def play_signal(bits):
    sample_rate, freq = 44100, 1000  # サンプリングレートと周波数（1kHz）
    for i, bit in enumerate(bits):
        duration = {'M': 0.8, '1': 0.5}.get(bit, 0.2)  # ビットに応じた長さ
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = 0.5 * np.sin(2 * np.pi * freq * t)  # 正弦波（1kHz）
        sd.play(wave, samplerate=sample_rate)  # 再生
        sd.wait()
        time.sleep(1 - duration)  # 1秒周期に調整

# Streamlit のプレースホルダー（動的出力用）
placeholder = st.empty()

# 再生ボタンが押されたときの処理
if st.button("リアルタイムJJY信号を再生開始"):
    st.info("リアルタイムJJY信号を再生中。時計をスピーカーに密着させてください")
    try:
        while True:
            # 現在の日本標準時を取得
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
            bits = make_jjy_bits(now)
            bit_display = [f"{i:02d}s: {bit}" for i, bit in enumerate(bits)]  # 各ビットを整形表示

            # ビット列を画面に表示
            placeholder.markdown(
                f"### 現在時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                + "```\n" + "\n".join(bit_display) + "\n```"
            )

            # 音声信号として出力
            play_signal(bits)
    except KeyboardInterrupt:
        st.warning("停止しました")
