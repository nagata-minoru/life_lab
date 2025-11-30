from nicegui import ui, app, run
import asyncio
import os
from typing import List

# # この環境ではプロセスプールの生成が許可されないため NiceGUI のプロセスプールを無効化する。
# # run.cpu_bound を使わない前提で PermissionError による起動失敗を防ぐ。
# run.process_pool = None
# run.setup = lambda: None

# ====== パラメータ ======
ROWS = 20
COLS = 30

# ====== 状態管理 ======
grid: List[List[int]] = [[0 for _ in range(COLS)] for _ in range(ROWS)]
running = False
speed_ms = 200 # 世代更新間隔（ミリ秒）
cell_buttons: List[List[ui.button]] = []
start_button = None

def count_neighbors(r: int, c: int) -> int:
  """
  指定したセル (r, c) の周囲8マスにある生存セル数をカウントする。

  盤面はトーラス（上下左右がつながる）として扱う。
  """
  cnt = 0
  for dr in [-1, 0, 1]:
    for dc in [-1, 0, 1]:
      if dr == 0 and dc == 0:
        continue
      nr = (r + dr) % ROWS
      nc = (c + dc) % COLS
      cnt += grid[nr][nc]
  return cnt

def step():
  """
  ライフゲームのルールに従い、盤面を1世代進める。

  生存:   隣接数が2または3のとき
  誕生:   隣接数が3のとき
  死滅:   それ以外
  """
  global grid
  new_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
  for r in range(ROWS):
    for c in range(COLS):
      n = count_neighbors(r, c)
      if grid[r][c] == 1:
        new_grid[r][c] = 1 if n in [2, 3] else 0
      else:
        new_grid[r][c] = 1 if n == 3 else 0
  grid = new_grid

def rebuild_grid():
  """
  現在の grid の状態を UI のボタン表示に反映する。

  生存セルは緑、死セルはアウトライン表示にする。
  """
  for r in range(ROWS):
    for c in range(COLS):
      btn = cell_buttons[r][c]
      if grid[r][c]:
        btn._props = {"color": "green"}
      else:
        btn._props = {"outline": True, "color": "gray"}
      btn.update()

async def run_loop():
  """
  実行中フラグが立っている間、一定間隔で世代更新を行う。

  NiceGUI のイベントループとは別に非同期タスクとして動作する。
  """
  global running
  while True:
    if running:
      step()
      rebuild_grid()
    await asyncio.sleep(speed_ms / 1000)

def toggle_running():
  """
  シミュレーションの実行／停止を切り替える。

  ボタンの表示テキストも連動して変更する。
  """
  global running
  running = not running
  if running:
    start_button.text = '⏸ ストップ'
  else:
    start_button.text = '▶ スタート'

def clear_grid():
  """
  すべてのセルを死状態にリセットする。
  """
  global grid
  for r in range(ROWS):
    for c in range(COLS):
      grid[r][c] = 0
  rebuild_grid()

def set_speed(value: int):
  """
  世代更新間隔（ms）を変更する。
  """
  global speed_ms
  speed_ms = value

def make_toggle_handler(rr: int, cc: int):
  """
  指定したセル (rr, cc) の状態をトグルするハンドラを生成する。
  """
  def toggle():
    grid[rr][cc] = 1 - grid[rr][cc]
    rebuild_grid()

  return toggle

# ====== UI構築 ======

def build_ui():
  global start_button, cell_buttons
  cell_buttons = []

  with ui.row().classes('w-full justify-between items-center'):
    ui.label('セル・オートマトン実験室（ライフゲーム）').classes('text-2xl font-bold')
    ui.button('クリア', on_click=lambda: clear_grid())

  with ui.row().classes('items-center gap-4'):
    start_button = ui.button('▶ スタート', on_click=toggle_running)
    ui.button('⏭ 1ステップ', on_click=lambda: (step(), rebuild_grid()))
    speed_slider = ui.slider(min=50, max=1000, value=speed_ms, step=50, on_change=lambda e: set_speed(e.value))
    speed_slider.label = 'スピード（ms）'

  # グリッド描画
  with ui.column().classes('gap-0'):
    for r in range(ROWS):
      row_buttons: List[ui.button] = []
      with ui.row().classes('gap-0'):
        for c in range(COLS):
          b = ui.button('', on_click=make_toggle_handler(r, c)).classes('w-6 h-6 min-w-0 m-0 p-0')
          row_buttons.append(b)
      cell_buttons.append(row_buttons)

  rebuild_grid()

# ====== 非同期タスク起動 ======

@app.on_startup
async def startup():
  """
  NiceGUI 起動時にバックグラウンドループを開始する。
  """
  asyncio.create_task(run_loop())

PORT = int(os.environ.get('PORT', '8080'))
HOST = os.environ.get('HOST', '0.0.0.0')

def run_app():
  """NiceGUI アプリを起動する（テストで安全に import できるよう関数化）。"""
  ui.run(build_ui, title='Life Lab', reload=False, port=PORT, host=HOST)


if __name__ == '__main__':
  run_app()
