import pytest

import main


class DummyButton:
  """NiceGUIのウィジェットを使わずrebuild_gridを動かすための最小スタブ。"""

  def __init__(self):
    """スタブボタンの状態を初期化する。"""
    self.last_props = None

  def props(self, value):
    """NiceGUIのprops呼び出しの代替として値を記録する。"""
    self.last_props = value


@pytest.fixture(autouse=True)
def reset_grid():
  """各テストの前後でグリッドとボタンの状態を初期化する。"""
  main.grid = [[0 for _ in range(main.COLS)] for _ in range(main.ROWS)]
  main.cell_buttons = [[DummyButton() for _ in range(main.COLS)] for _ in range(main.ROWS)]
  yield
  main.running = False
  main.speed_ms = 200


def test_count_neighbors_wraps_around_edges():
  """端をまたいだ近傍セルを正しくカウントできることを確認する。"""
  neighbors = [
    (main.ROWS - 1, main.COLS - 1),
    (main.ROWS - 1, 0),
    (0, main.COLS - 1),
  ]
  for r, c in neighbors:
    main.grid[r][c] = 1

  assert main.count_neighbors(0, 0) == 3


def test_step_keeps_block_stable():
  """安定配置（ブロック）がステップ後も変化しないことを確認する。"""
  live_cells = [(5, 5), (5, 6), (6, 5), (6, 6)]
  for r, c in live_cells:
    main.grid[r][c] = 1

  main.step()

  for r, c in live_cells:
    assert main.grid[r][c] == 1
  assert main.grid[5][4] == 0
  assert main.grid[4][5] == 0


def test_step_oscillates_blinker():
  """オシレータ（ブリンカー）がステップで縦横に交互に変化することを確認する。"""
  for c in [5, 6, 7]:
    main.grid[6][c] = 1

  main.step()

  expected = {(5, 6), (6, 6), (7, 6)}
  alive = {(r, c) for r in range(main.ROWS) for c in range(main.COLS) if main.grid[r][c] == 1}
  assert alive == expected


def test_make_toggle_handler_updates_grid_and_button_state():
  """トグルハンドラがグリッドとボタン状態を適切に更新することを確認する。"""
  toggle = main.make_toggle_handler(0, 0)

  toggle()
  assert main.grid[0][0] == 1
  assert main.cell_buttons[0][0].last_props == "color=red"

  toggle()
  assert main.grid[0][0] == 0
  assert main.cell_buttons[0][0].last_props == "outline color=gray"
