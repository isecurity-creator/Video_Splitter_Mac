import ffmpeg
import tkinter
import tkinter.filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import ctypes
import os
import json
import threading
import time

progress_list = [False, False]


def video_load():
    global video_file_path, thumbnail_label, thumbnail_image, video_ext
    # 動画ファイルを選択
    video_file_path = tkinter.filedialog.askopenfilename(title="ファイル選択", initialdir= os.path.abspath(os.path.dirname(__file__)), filetypes=[("Video File", "*.mp4;*.mov;*.avi;*.mkv;*.wmv;*.flv")]    )
    # ファイルが選択されなかった場合
    if not video_file_path:
        tkinter.messagebox.showwarning("エラー", "ファイルが選択されませんでした。")
        thumbnail_label.config(text="ファイルが選択されていません", image="")
        progress_list[0] = False
        video_file_input_complete_lavel.config(text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red")
        return
    print(f"選択されたビデオのパス: {video_file_path}")
    #表示を買える
    video_file_input_complete_lavel.config(text="読込中...", font=("游ゴシック",int(app_height *0.025), "bold"), fg="orange")
    # 拡張子チェック（動画ファイルかどうか）
    valid_ext = (".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv")
    #後で利用するため拡張子のみを取り出し
    _, ext = os.path.splitext(video_file_path)
    video_ext = ext.lower()
    print(f"入力動画の拡張子:{video_ext}")
    if not video_file_path.lower().endswith(valid_ext):
        tkinter.messagebox.showwarning("エラー", "動画ファイルを選択してください。")
        thumbnail_label.config(text="エラー: 動画ファイルを選択してください。", image="")
        progress_list[0] = False
        video_file_input_complete_lavel.config(text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red")
        return
    # 一時サムネイルパス
    thumbnail_path = "thumbnail_temp.jpg"
    try:
        # ffmpegを使って1秒地点のフレームをサムネイルとして抽出
        command = [
            "ffmpeg",
            "-y",              # 既存ファイルを上書き
            "-i", video_file_path,
            "-ss", "00:00:01",
            "-vframes", "1",
            thumbnail_path
        ]
        # 実行結果をチェック
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8'
        )
        # ffmpegがエラーを出した場合
        if result.returncode != 0 or not os.path.exists(thumbnail_path):
            tkinter.messagebox.showerror("エラー","ffmpegによるサムネイル生成に失敗しました。")
            print(result.stderr)
            thumbnail_label.config(text="エラー: サムネイル生成に失敗しました。", image="")
            progress_list[0] = False
            video_file_input_complete_lavel.config(text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red")
            return
        # サムネイル画像を表示
        image = Image.open(thumbnail_path)
        image.thumbnail((int(app_width*0.45), int(app_height*0.8)))
        thumbnail_image = ImageTk.PhotoImage(image)
        thumbnail_label.config(image=thumbnail_image, text="")
        thumbnail_label.image = thumbnail_image
        #tkinter.messagebox.showinfo("読み込み成功", f"動画を読み込みました。\n選択されたファイルパス:\n{video_file_path}")
        progress_list[0] = True
        video_file_input_complete_lavel.config(text="読込完了", font=("游ゴシック",int(app_height *0.025), "bold"), fg="green")
    except FileNotFoundError:
        # ffmpegがインストールされていない場合
        tkinter.messagebox.showerror("エラー", "ffmpegが見つかりません。")
        thumbnail_label.config(text="エラー: ffmpegがインストールされていません。", image="")
        progress_list[0] = False
        video_file_input_complete_lavel.config(text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red")
    except Exception as e:
        tkinter.messagebox.showerror("予期せぬエラー" ,f"不明なエラーが発生しました: {e}\n開発者にこのエラーを伝えてください。")
        thumbnail_label.config(text=f"エラー: {e}", image="")
        progress_list[0] = False
        video_file_input_complete_lavel.config(text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red")
    finally:
        # 一時ファイルの削除（存在する場合のみ）
        if os.path.exists(thumbnail_path):
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
        output_dir_select_complete_lavel.config(text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red")
        selected_dir_display.config(text="ここに選択したディレクトリが表示されます。")
    else:
        #tkinter.messagebox.showinfo("選択成功", f"出力先ディレクトリを選択しました。\n選択されたディレクトリパス:\n{output_dir_path}")
        progress_list[1] = True
        output_dir_select_complete_lavel.config(text="選択済", font=("游ゴシック",int(app_height *0.025), "bold"), fg="green")
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
    prw_app_width = int(screen_width * 0.2)
    prw_app_height = int((screen_height - taskbar_height) * 0.2)
    process_window.geometry(f"{prw_app_width}x{prw_app_height}")
    #サブウィンドウの大きさの変更を禁止
    process_window.resizable(False, False)
    #親Windowをいじれないようにする
    process_window.grab_set()
    #バツボタンで閉じることを禁止
    process_window.protocol('WM_DELETE_WINDOW', lambda: None)
    #説明を追記
    under_process_info = tkinter.Label(process_window, text="処理中です\nしばらくお待ちください", font=("游ゴシック",int(prw_app_width *0.04), "bold"), justify="center")
    under_process_info.place(relx=0, rely=0.04, relwidth=1)
    #プログレスバー
    progress_percentage = tkinter.IntVar()
    progress_bar = ttk.Progressbar(process_window, maximum=100, orient="horizontal", mode="determinate", variable=progress_percentage)
    progress_bar.place(relx=0.1, rely=0.35, relwidth=0.8, relheight=0.18)
    #進捗文字表記
    progress_text = tkinter.Label(process_window, text=f"\nただいま0個中0個目を処理中(0%)", font=("游ゴシック",int(prw_app_width *0.033)), justify="center")
    progress_text.place(relx=0, rely=0.6, relwidth=1)
    #キャンセルボタン
    global stop_button
    stop_button = tkinter.Button(process_window, text="キャンセル", command=cancel_flag_lettrue,  font=("游ゴシック",int(app_height *0.020)))
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


# ウィンドウを作成
main = tkinter.Tk()
main.title("動画分割")
try:
    # 画面サイズを取得（タスクバーを除く）
    user32 = ctypes.windll.user32
    # 画面の横幅
    screen_width = user32.GetSystemMetrics(0)
    # 画面の縦幅（タスクバー含む）
    screen_height = user32.GetSystemMetrics(1)
    # タスクバーの高さ
    taskbar_height = user32.GetSystemMetrics(4)
    # タスクバーを考慮したウィンドウサイズを設定
    app_width = int(screen_width * 0.5)
    app_height = int((screen_height - taskbar_height) * 0.5)
    main.geometry(f"{app_width}x{app_height}")
except:
    app_width = 1200
    app_height = 1000
    main.geometry(str(1200) + "x" + str(1000))
#ウィンドウサイズを絶対的に指定する場合はこれを使う
#main.geometry(str(WIDTH) + "x" + str(HEIGHT))
# ウィンドウサイズの変更を禁止
main.resizable(False, False)

#画像を表示するエリア
thumbnail_label = tkinter.Label(main, text="ここにサムネイルが表示されます", font=("游ゴシック",int(app_height *0.020)), bg="#A4A4A4")
thumbnail_label.place(relx=0.5, rely=0.1, relwidth=0.45, relheight=0.8)

#説明1
desc1 = tkinter.Label(main, text="手順1\n　分割したい動画ファイルを選択\n", font=("游ゴシック",int(app_height *0.025)), justify="left")
desc1.place(relx=0.02, rely=0.01)

#動画読み込みボタン
video_file_load_button = tkinter.Button(main, text="動画ファイルを選択", command=video_load, font=("游ゴシック",int(app_height *0.020)), bg="#eac9f1", fg="#000000")
video_file_load_button.place(relx=0.05, rely=0.12, relwidth=0.2, relheight=0.08)

#読み込み完了表示
video_file_input_complete_lavel = tkinter.Label(main, text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red", justify="left")
video_file_input_complete_lavel.place(relx=0.27, rely=0.13)

#説明2
desc2 = tkinter.Label(main, text="手順2\n　分割する間隔を入力", font=("游ゴシック",int(app_height *0.025)), justify="left")
desc2.place(relx=0.02, rely=0.24)

#入力部分
input_min = tkinter.Entry(main, font=("游ゴシック",int(app_height *0.025)), justify="right")
input_min.place(relx=0.05, rely=0.38, relwidth=0.07, relheight=0.06)
input_min.insert(0, "3")
input_sec = tkinter.Entry(main, font=("游ゴシック",int(app_height *0.025)), justify="right")
input_sec.place(relx=0.16, rely=0.38, relwidth=0.07, relheight=0.06)
input_sec.insert(0, "0")
#説明
desc_min = tkinter.Label(main, text="分", font=("游ゴシック",int(app_height *0.025)), justify="left")
desc_min.place(relx=0.13, rely=0.38)
desc_sec = tkinter.Label(main, text="秒ずつに分割", font=("游ゴシック",int(app_height *0.025)), justify="left")
desc_sec.place(relx=0.24, rely=0.38)

#説明3
desc3 = tkinter.Label(main, text="手順3\n　出力先ディレクトリの選択", font=("游ゴシック",int(app_height *0.025)), justify="left")
desc3.place(relx=0.02, rely=0.48)

#出力ディレクトリ選択
output_dir_select_button = tkinter.Button(main, text="出力先ディレクトリを選択", command=output_dir_select,  font=("游ゴシック",int(app_height *0.020)), bg="#c9eff1", fg="#000000")
output_dir_select_button.place(relx=0.05, rely=0.59, relwidth=0.2, relheight=0.08)

#ディレクトリ選択完了表示
output_dir_select_complete_lavel = tkinter.Label(main, text="未選択", font=("游ゴシック",int(app_height *0.025), "bold"), fg="red", justify="left")
output_dir_select_complete_lavel.place(relx=0.27, rely=0.605)

selected_dir_display = tkinter.Label(main, text="ここに選択したディレクトリが表示されます。", font=("游ゴシック",int(app_height *0.015)), justify="left")
selected_dir_display.place(relx=0.04, rely=0.7)

#説明4
desc4 = tkinter.Label(main, text="手順4\n　処理開始", font=("游ゴシック",int(app_height *0.025)), justify="left")
desc4.place(relx=0.02, rely=0.76)

#処理開始
output_dir_select_button = tkinter.Button(main, text="処理開始", command=start_process,  font=("游ゴシック",int(app_height *0.020)), bg="#c9f1d1", fg="#000000")
output_dir_select_button.place(relx=0.05, rely=0.87, relwidth=0.2, relheight=0.08)

# イベントループ
main.mainloop()