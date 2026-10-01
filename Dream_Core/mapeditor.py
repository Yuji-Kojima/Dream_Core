import json
import tkinter as tk
from tkinter import filedialog, messagebox


class MapEditor:

    def __init__(self, root, width=15, height=9, cell_size=40):
        self.root = root
        self.width = width
        self.height = height
        self.cell_size = cell_size

        self.root.title("15x9 マップエディタ")

        # 0: 床, 1: 壁, 2: 敵
        self.current_tile = 1  # 初期選択は「壁(1)」
        self.grid_data = [[0 for _ in range(width)] for _ in range(height)]

        # マス目の色設定
        self.tile_colors = {
            0: "#FFFFFF",  # 床: 白
            1: "#333333",  # 壁: ダークグレー
            2: "#FF4D4D",  # 敵: 赤
        }

        self._create_widgets()
        self._draw_grid()

    def _create_widgets(self):
        # メインフレーム
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack()

        # パレット（タイル選択ラジオボタン）
        palette_frame = tk.LabelFrame(main_frame, text=" タイル選択 ", padx=10, pady=5)
        palette_frame.pack(fill="x", pady=(0, 10))

        self.tile_var = tk.IntVar(value=self.current_tile)
        tk.Radiobutton(
            palette_frame,
            text="床 (0)",
            variable=self.tile_var,
            value=0,
            command=self._update_selected_tile,
        ).pack(side="left", padx=5)
        tk.Radiobutton(
            palette_frame,
            text="壁 (1)",
            variable=self.tile_var,
            value=1,
            command=self._update_selected_tile,
        ).pack(side="left", padx=5)
        tk.Radiobutton(
            palette_frame,
            text="敵 (2)",
            variable=self.tile_var,
            value=2,
            command=self._update_selected_tile,
        ).pack(side="left", padx=5)

        # 描画キャンバス
        canvas_w = self.width * self.cell_size
        canvas_h = self.height * self.cell_size
        self.canvas = tk.Canvas(
            main_frame, width=canvas_w, height=canvas_h, bg="#FFFFFF"
        )
        self.canvas.pack()

        # マウスイベントのバインド
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)

        # 操作用ボタンバー
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        tk.Button(
            btn_frame,
            text="配列出力 (Print)",
            command=self.print_map,
            bg="#E1E1E1",
        ).pack(side="left", padx=2)
        tk.Button(
            btn_frame, text="クリア (全床)", command=self.clear_map
        ).pack(side="left", padx=2)
        tk.Button(
            btn_frame, text="JSON保存", command=self.save_json
        ).pack(side="right", padx=2)
        tk.Button(
            btn_frame, text="JSON読込", command=self.load_json
        ).pack(side="right", padx=2)

    def _update_selected_tile(self):
        self.current_tile = self.tile_var.get()

    def _draw_grid(self):
        self.canvas.delete("all")
        for y in range(self.height):
            for x in range(self.width):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                tile_val = self.grid_data[y][x]
                color = self.tile_colors.get(tile_val, "#FFFFFF")

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#CCCCCC"
                )

                # マス目に数値をテキスト表示（確認しやすくするため）
                text_color = "#FFFFFF" if tile_val == 1 else "#000000"
                self.canvas.create_text(
                    x1 + self.cell_size / 2,
                    y1 + self.cell_size / 2,
                    text=str(tile_val),
                    fill=text_color,
                    font=("Helvetica", 10, "bold"),
                )

    def _set_tile_at_position(self, event):
        x = event.x // self.cell_size
        y = event.y // self.cell_size

        if 0 <= x < self.width and 0 <= y < self.height:
            if self.grid_data[y][x] != self.current_tile:
                self.grid_data[y][x] = self.current_tile
                self._draw_grid()

    def _on_canvas_click(self, event):
        self._set_tile_at_position(event)

    def _on_canvas_drag(self, event):
        self._set_tile_at_position(event)

    # --- 外部連携・便利メソッド ---

    def get_map_data(self):
        """現在のマップデータ（9行15列の二次元配列）を取得"""
        return self.grid_data

    def print_map(self):
        """コンソールにPythonコード形式で出力"""
        print("--- マップ配列 (15x9) ---")
        print("MAP = [")
        for row in self.grid_data:
            print(f"    {row},")
        print("]")

    def clear_map(self):
        """すべて床（0）でリセット"""
        self.grid_data = [
            [0 for _ in range(self.width)] for _ in range(self.height)
        ]
        self._draw_grid()

    def save_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.grid_data, f)
            messagebox.showinfo("成功", "ファイルに保存しました。")

    def load_json(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if len(data) == self.height and len(data[0]) == self.width:
                        self.grid_data = data
                        self._draw_grid()
                    else:
                        messagebox.showerror(
                            "エラー", "マップサイズが15x9と一致しません。"
                        )
            except Exception as e:
                messagebox.showerror(
                    "エラー", f"読み込みに失敗しました:\n{e}"
                )


# --- 呼び出し用の実行コード ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MapEditor(root, width=15, height=9)
    root.mainloop()