import ffmpeg
import tkinter
import tkinter.filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
#import ctypes
import os
import json
import threading
import time
import tempfile

progress_list = [False, False]


VALID_VIDEO_EXT = (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv")

def set_video_status(text, color):
    video_file_input_complete_lavel.config(text=text, fg=color)

def clear_thumbnail(message):
    thumbnail_label.config(text=message, image="")
    thumbnail_label.image = None

def video_load():
    global video_file_path, thumbnail_image, video_ext
    video_file_path = tkinter.filedialog.askopenfilename(
        title="ファイル選択",
        initialdir=os.path.abspath(os.path.dirname(__file__)),
        filetypes=[
            ("Video File", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv"),
            ("All Files", "*.*"),
        ],
    )
    if not video_file_path:
        tkinter.messagebox.showwarning("エラー", "ファイルが選択されませんでした。")
        clear_thumbnail("ファイルが選択されていません")
        progress_list[0] = False
        set_video_status("未選択", "red")
        return
    _, ext = os.path.splitext(video_file_path)
    video_ext = ext.lower()
    if video_ext not in VALID_VIDEO_EXT:
        tkinter.messagebox.showwarning("エラー", "動画ファイルを選択してください。")
        clear_thumbnail("エラー: 動画ファイルを選択してください。")
        progress_list[0] = False
        set_video_status("未選択", "red")
        return
    set_video_status("読込中...", "orange")
    main.update_idletasks()
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            thumbnail_path = tmp.name
        command = [
            "ffmpeg",
            "-y",
            "-ss", "00:00:01",
            "-i", video_file_path,
            "-vframes", "1",
            thumbnail_path,
        ]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0 or not os.path.exists(thumbnail_path):
            tkinter.messagebox.showerror("エラー", "ffmpegによるサムネイル生成に失敗しました。")
            print(result.stderr)
            clear_thumbnail("エラー: サムネイル生成に失敗しました。")
            progress_list[0] = False
            set_video_status("未選択", "red")
            return
        image = Image.open(thumbnail_path)
        # 現在のサムネイル表示領域のサイズを取得
        thumbnail_label.update_idletasks()
        label_width = thumbnail_label.winfo_width()
        label_height = thumbnail_label.winfo_height()
        # まだサイズが確定していない場合の保険
        if label_width <= 1 or label_height <= 1:
            label_width = 64
            label_height = 360
        image.thumbnail((label_width, label_height))
        thumbnail_image = ImageTk.PhotoImage(image)
        thumbnail_label.config(image=thumbnail_image, text="")
        thumbnail_label.image = thumbnail_image
        progress_list[0] = True
        set_video_status("読込完了", "green")
    except FileNotFoundError:
        tkinter.messagebox.showerror("エラー", "ffmpegが見つかりません。")
        clear_thumbnail("エラー: ffmpegがインストールされていません。")
        progress_list[0] = False
        set_video_status("未選択", "red")
    except Exception as e:
        tkinter.messagebox.showerror(
            "予期せぬエラー",
            f"不明なエラーが発生しました: {e}\n開発者にこのエラーを伝えてください。",
        )
        clear_thumbnail(f"エラー: {e}")
        progress_list[0] = False
        set_video_status("未選択", "red")
    finally:
        if "thumbnail_path" in locals() and os.path.exists(thumbnail_path):
            try:
                os.remove(thumbnail_path)
            except Exception:
                pass


def get_video_duration():
    """
    ffprobeを使って動画の長さ（秒）を取得する。
    成功時はfloat（秒）、失敗時はNoneを返す。
    """
    try:
        # ffprobeコマンドを実行（JSON形式で出力）
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            video_file_path
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        # ffprobeの出力をJSONとしてパース
        info = json.loads(result.stdout)
        # duration値を取得
        duration = float(info["format"]["duration"])
        return duration
    except Exception as e:
        print(f"動画の長さ取得に失敗しました:\n{e}\nこのエラーコードを開発者に伝えてください。")
        return None


def output_dir_select():
    global output_dir_path
    output_dir_path = tkinter.filedialog.askdirectory(initialdir=os.path.abspath(os.path.dirname(__file__)))
    if not output_dir_path:
        progress_list[1] = False
        output_dir_select_complete_lavel.config(text="未選択", fg="red")
        selected_dir_display.config(text="ここに選択したディレクトリが表示されます。")
    else:
        #tkinter.messagebox.showinfo("選択成功", f"出力先ディレクトリを選択しました。\n選択されたディレクトリパス:\n{output_dir_path}")
        progress_list[1] = True
        output_dir_select_complete_lavel.config(text="選択済", fg="green")
        selected_dir_display.config(text=output_dir_path)
        return


def sec_to_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02}:{m:02}:{s:02}"


def video_trim(start_time, end_time, filename):
    global process_success, current_process_finished
    output_path = os.path.join(output_dir_path, f"{filename}{video_ext}")
    try:
        # ffmpeg-python では「to=」を使用する
        start_tc = sec_to_time(start_time)
        end_tc = sec_to_time(end_time)
        process_stream = ffmpeg.input(video_file_path, ss=start_tc, to=end_tc).output(output_path).overwrite_output()
        ffmpeg.run(process_stream, capture_stdout=True, capture_stderr=True)
        print(f"出力完了: {output_path}")
        process_success = True
    except Exception as e:
        print(f"処理中にエラーが発生しました:\n{e}\nこのコードを開発者に伝えてください。")
        process_success = False
    finally:
        current_process_finished = True


def cancel_flag_lettrue():
    global cancel_flag, stop_button, process_window
    process_window.update()
    cancel_flag = True
    stop_button.config(text="キャンセル処理中")


def start_process():
    #準備ができているか確認
    if not progress_list[0]:
        tkinter.messagebox.showerror("エラー", "処理前の動画ファイルが未選択、または読み込みエラーになっています。")
        return
    if not progress_list[1]:
        tkinter.messagebox.showerror("エラー", "出力先ディレクトリが未選択です。")
        return
    #間隔取得
    trim_interval_min = input_min.get()
    trim_interval_sec = input_sec.get()
    trim_interval_min = int(trim_interval_min)
    trim_interval_sec = int(trim_interval_sec)
    trim_interval = (trim_interval_min * 60) + trim_interval_sec
    if trim_interval < 1:
        tkinter.messagebox.showerror("エラー", "分割間隔(分,秒)の設定値が不適切です。")
        return
    original_video_time = get_video_duration()
    if original_video_time < trim_interval:
        tkinter.messagebox.showerror("エラー", "処理前の動画よりも長い時間で分割することはできません。")
        return
    #処理の下準備
    tkinter.messagebox.showinfo("処理開始", "処理を開始します。\n動画の長さによっては、処理に時間がかかることがあります。\n処理中は可能な限り他の操作を行わないでください。")
    print("処理開始")
    #変数の初期設定
    global process_success, cancel_flag, current_process_finished
    process_success = True
    cancel_flag = False
    current_process_finished = True
    #処理の進捗を表示するサブウィンドウ
    global process_window
    process_window = tkinter.Toplevel(main)
    process_window.title("処理中")
    prw_app_width = int(screen_width * 0.3)
    prw_app_height = int(screen_height * 0.3)
    process_window.geometry(f"{prw_app_width}x{prw_app_height}")
    #サブウィンドウの大きさの変更を禁止
    process_window.resizable(False, False)
    #親Windowをいじれないようにする
    process_window.grab_set()
    #バツボタンで閉じることを禁止
    process_window.protocol('WM_DELETE_WINDOW', lambda: None)
    #説明を追記
    under_process_info = tkinter.Label(process_window, text="処理中です\nしばらくお待ちください", font=FONT_BOLD, justify="center")
    under_process_info.place(relx=0, rely=0.04, relwidth=1)
    #プログレスバー
    progress_percentage = tkinter.IntVar()
    progress_bar = ttk.Progressbar(process_window, maximum=100, orient="horizontal", mode="determinate", variable=progress_percentage)
    progress_bar.place(relx=0.1, rely=0.35, relwidth=0.8, relheight=0.18)
    #進捗文字表記
    progress_text = tkinter.Label(process_window, text=f"\nただいま0個中0個目を処理中(0%)", font=FONT_NORMAL, justify="center")
    progress_text.place(relx=0, rely=0.6, relwidth=1)
    #キャンセルボタン
    global stop_button
    stop_button = tkinter.Button(process_window, text="キャンセル", command=cancel_flag_lettrue, font=FONT_NORMAL)
    stop_button.place(relx=0.3, rely=0.85, relwidth=0.4, relheight=0.1)
    #process_window.mainloop()
    #↑だとここで実行が止まる
    process_window.update()
    #分割数の確認
    if original_video_time % trim_interval < 1:
        split_num = (original_video_time // trim_interval)
    else:
        split_num = (original_video_time // trim_interval) + 1
    split_num = int(split_num)
    #時間管理
    start_time = 0
    end_time = 0
    #ファイル名の継承
    original_file_name = os.path.splitext(os.path.basename(video_file_path))[0]
    #while文関係の準備
    i = 0
    cancel_flag = False
    #サブウィンドウ関係の準備
    progress_text.config(text=f"\nただいま{split_num}個中0個目を処理中です。")
    #全件処理
    while i < split_num and process_success and not cancel_flag:
        if i == 0:
            #完了個数が0のとき
            progress_text.config(text=f"\nただいま{split_num}個中{i+1}個目を処理中です。")
        else:
            progress_text.config(text=f"{split_num}個中{i}個は処理が終わりました。({int(i/split_num*100)}%)\nただいま{i+1}個目を処理中です。")
        #プログレスバー動かす
        progress_percentage.set(int((i)/split_num*100))
        process_window.update()
        #時間計算
        end_time = start_time + trim_interval
        if end_time > original_video_time:
            end_time = original_video_time
        #ファイル名
        output_file_name = original_file_name + "_" + str(i+1)
        #処理呼び出し(サブプロセス)
        current_process_finished = False
        sub_process_thread = threading.Thread(target=video_trim, args=(start_time, end_time, output_file_name))
        sub_process_thread.start()
        #終了までサブウィンドウを動かしたまま待機
        while not current_process_finished:
            process_window.update()
            time.sleep(0.1)
        #process_success = video_trim(start_time, end_time, output_file_name)
        #次の準備
        start_time = end_time
        #疑似for文
        i += 1
    process_window.destroy()
    if cancel_flag:
        print("中断")
        tkinter.messagebox.showinfo("処理中断", "ユーザー操作により処理を中断しました。")
    elif process_success:
        print("処理完了")
        tkinter.messagebox.showinfo("処理完了", "処理が終了しました。")
    else:
        print("エラーにより中断")
        tkinter.messagebox.showerror("処理が未完了", "エラーが発生した、またはユーザーによって中断されたため、処理を中断しました。")
    return


main = tkinter.Tk()
main.title("動画分割")
screen_width = main.winfo_screenwidth()
screen_height = main.winfo_screenheight()
app_width = int(screen_width * 0.7)
app_height = int(screen_height * 0.7)
main.geometry(f"{app_width}x{app_height}")
main.minsize(900, 650)
main.resizable(True, True)
FONT_NORMAL = ("Helvetica", 14)
FONT_LARGE = ("Helvetica", 16)
FONT_BOLD = ("Helvetica", 16, "bold")
FONT_SMALL = ("Helvetica", 11)
# 全体を左右2カラムにする
main.columnconfigure(0, weight=1)
main.columnconfigure(1, weight=2)
main.rowconfigure(0, weight=1)
left_frame = tkinter.Frame(main, padx=20, pady=20)
left_frame.grid(row=0, column=0, sticky="nsew")
right_frame = tkinter.Frame(main, padx=20, pady=20)
right_frame.grid(row=0, column=1, sticky="nsew")
# 左側フレームの列設定
left_frame.columnconfigure(0, weight=1)
left_frame.columnconfigure(1, weight=1)
# 右側フレーム
right_frame.rowconfigure(0, weight=1)
right_frame.columnconfigure(0, weight=1)
thumbnail_label = tkinter.Label(
    right_frame,
    text="ここにサムネイルが表示されます",
    font=FONT_NORMAL,
    bg="#A4A4A4"
)
thumbnail_label.grid(row=0, column=0, sticky="nsew")

# 手順1
desc1 = tkinter.Label(
    left_frame,
    text="手順1\n分割したい動画ファイルを選択",
    font=FONT_LARGE,
    justify="left"
)

desc1.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

video_file_load_button = tkinter.Button(
    left_frame,
    text="動画ファイルを選択",
    command=video_load,
    font=FONT_NORMAL,
    bg="#eac9f1",
    fg="#000000"
)

video_file_load_button.grid(row=1, column=0, sticky="ew", pady=(0, 20))

video_file_input_complete_lavel = tkinter.Label(
    left_frame,
    text="未選択",
    font=FONT_BOLD,
    fg="red",
    justify="left"
)

video_file_input_complete_lavel.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(0, 20))

# 手順2
desc2 = tkinter.Label(
    left_frame,
    text="手順2\n分割する間隔を入力",
    font=FONT_LARGE,
    justify="left"
)

desc2.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))
time_frame = tkinter.Frame(left_frame)
time_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 20))
input_min = tkinter.Entry(time_frame, font=FONT_NORMAL, justify="right", width=5)
input_min.pack(side="left")
input_min.insert(0, "3")
desc_min = tkinter.Label(time_frame, text="分", font=FONT_NORMAL)
desc_min.pack(side="left", padx=(5, 15))
input_sec = tkinter.Entry(time_frame, font=FONT_NORMAL, justify="right", width=5)
input_sec.pack(side="left")
input_sec.insert(0, "0")
desc_sec = tkinter.Label(time_frame, text="秒ずつに分割", font=FONT_NORMAL)
desc_sec.pack(side="left", padx=(5, 0))

# 手順3
desc3 = tkinter.Label(
    left_frame,
    text="手順3\n出力先ディレクトリの選択",
    font=FONT_LARGE,
    justify="left"
)
desc3.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 10))
output_dir_select_button = tkinter.Button(
    left_frame,
    text="出力先ディレクトリを選択",
    command=output_dir_select,
    font=FONT_NORMAL,
    bg="#c9eff1",
    fg="#000000"
)
output_dir_select_button.grid(row=5, column=0, sticky="ew", pady=(0, 10))
output_dir_select_complete_lavel = tkinter.Label(
    left_frame,
    text="未選択",
    font=FONT_BOLD,
    fg="red",
    justify="left"
)
output_dir_select_complete_lavel.grid(row=5, column=1, sticky="w", padx=(10, 0), pady=(0, 10))
selected_dir_display = tkinter.Label(
    left_frame,
    text="ここに選択したディレクトリが表示されます。",
    font=FONT_SMALL,
    justify="left",
    wraplength=350
)
selected_dir_display.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 20))

# 手順4
desc4 = tkinter.Label(
    left_frame,
    text="手順4\n処理開始",
    font=FONT_LARGE,
    justify="left"
)
desc4.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 10))
start_button = tkinter.Button(
    left_frame,
    text="処理開始",
    command=start_process,
    font=FONT_NORMAL,
    bg="#c9f1d1",
    fg="#000000"
)
start_button.grid(row=8, column=0, sticky="ew")

main.mainloop()