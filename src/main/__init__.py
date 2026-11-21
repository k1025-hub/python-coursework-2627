# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    if max_hp <= 0:
        return 0

    percentage = int(hp * 100 / max_hp)
    return max(0, min(100, percentage))


def status_report(name, robot_type, hp, max_hp, battery):
    hp_percent = hp_ratio(hp, max_hp)

    if battery >= 60:
        battery_status = "OK"
    elif battery >= 20:
        battery_status = "WARNING"
    else:
        battery_status = "LOW"

    return (f"{name:<10}|{robot_type:^10}|HP {hp_percent:>3}%|"
            f"BAT {battery:>3}%|{battery_status}")


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    by_armor = {"front": 0, "left": 0, "right": 0}
    seen_ids = set()
    damages = []

    sensor_map = {
        "F": "front",
        "L": "left",
        "R": "right",
    }

    for line in lines:
        try:
            if not isinstance(line, str):
                continue

            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("{"):
                record = json.loads(line)

                if not isinstance(record, dict):
                    continue

                armor = record.get("armor")
                damage = record.get("damage")

                if armor not in by_armor:
                    continue
                if (not isinstance(damage, int)
                        or isinstance(damage, bool)
                        or damage <= 0):
                    continue

                if "id" in record:
                    record_id = json.dumps(record["id"], sort_keys=True)
                    if record_id in seen_ids:
                        continue
                    seen_ids.add(record_id)

                by_armor[armor] += damage
                damages.append(damage)

            else:
                parts = line.split(",")
                parsed = []
                used_labels = set()
                valid = bool(parts)

                for part in parts:
                    if part.count(":") != 1:
                        valid = False
                        break

                    label, value = part.split(":")

                    if label not in sensor_map or label in used_labels:
                        valid = False
                        break

                    if (not value.isascii()
                            or not value.isdigit()
                            or int(value) <= 0):
                        valid = False
                        break                    

                    used_labels.add(label)
                    parsed.append((sensor_map[label], int(value)))

                if not valid or not parsed:
                    continue

                for armor, damage in parsed:
                    by_armor[armor] += damage
                    damages.append(damage)
                    
        except Exception:
            continue
        

    total = sum(damages)

    if total == 0:
        most_hit = None
        average = 0.0
    else:
        most_hit = max(by_armor, key=by_armor.get)
        average = round(total / len(damages), 2)

    return {
        "total": total,
        "by_armor": by_armor,
        "most_hit": most_hit,
        "avg": average,
    }

# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self._pos = self._clamp_cell(start_pos)
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("当前位置需要长度为 2 的 tuple/list")

        self._pos = self._clamp_cell(value)


    def move_forward(self):
        if self._fuel <= 0:
            return self._pos

        self._fuel -= 1
        dx, dy = self._facing.delta
        next_x = self._pos[0] + dx
        next_y = self._pos[1] + dy

        if self.is_blocked(next_x, next_y):
            self._collision_count += 1
            return self._pos

        self._pos = (next_x, next_y)
        return self._pos


    def turn_left(self):
        left_turn = {
            Facing.UP: Facing.LEFT,
            Facing.LEFT: Facing.DOWN,
            Facing.DOWN: Facing.RIGHT,
            Facing.RIGHT: Facing.UP,
        }
        self._facing = left_turn[self._facing]
        return self._facing


    def turn_right(self):
        right_turn = {
            Facing.UP: Facing.RIGHT,
            Facing.RIGHT: Facing.DOWN,
            Facing.DOWN: Facing.LEFT,
            Facing.LEFT: Facing.UP,
        }
        self._facing = right_turn[self._facing]
        return self._facing    


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    x, y = pos
    target_x, target_y = target

    current_distance = abs(x - target_x) + abs(y - target_y)
    candidates = []

    for facing in (Facing.UP, Facing.DOWN, Facing.LEFT, Facing.RIGHT):
        dx, dy = facing.delta
        next_pos = (x + dx, y + dy)

        if next_pos in obstacles:
            continue

        next_distance = (abs(next_pos[0] - target_x)
                         + abs(next_pos[1] - target_y))

        if next_distance < current_distance:
            candidates.append(facing)

    if not candidates:
        return current_facing

    x_gap = abs(target_x - x)
    y_gap = abs(target_y - y)

    if x_gap >= y_gap:
        preferred = Facing.RIGHT if target_x > x else Facing.LEFT
        fallback = Facing.UP if target_y > y else Facing.DOWN
    else:
        preferred = Facing.UP if target_y > y else Facing.DOWN
        fallback = Facing.RIGHT if target_x > x else Facing.LEFT

    if preferred in candidates:
        return preferred
    if fallback in candidates:
        return fallback

    return candidates[0]


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


def decide(sensor, state, hp, heat):
    required_fields = {
        "enemy_frames",
        "enemy_dist",
        "robot_type",
        "max_hp",
    }

    if not isinstance(sensor, dict) or not required_fields.issubset(sensor):
        raise ValueError("sensor 缺少必要字段")

    if not isinstance(state, SentryState):
        raise ValueError("state 必须是 SentryState")

    enemy_frames = sensor["enemy_frames"]

    if isinstance(enemy_frames, (tuple, list)):
        if not 1 <= len(enemy_frames) <= 6:
            raise ValueError("enemy_frames 长度必须为 1 到 6")
        enemy_frames = tuple(bool(frame) for frame in enemy_frames)
    else:
        # 字段存在但值不合法：防御式地视为当前未发现敌人
        enemy_frames = (False,)

    def to_int(value, default):
        if isinstance(value, bool):
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    max_hp = to_int(sensor["max_hp"], 0)
    hp_value = to_int(hp, 0)
    hp_pct = hp_ratio(hp_value, max_hp)

    enemy_dist = sensor["enemy_dist"]
    if (isinstance(enemy_dist, bool)
            or not isinstance(enemy_dist, int)
            or enemy_dist < 0):
        enemy_dist = 999999

    robot_type = sensor["robot_type"]
    if robot_type != "HERO":
        robot_type = "INFANTRY"

    visible = enemy_frames[-1]

    def engage_action():
        if enemy_dist <= 3:
            return "SHOOT", SentryState.ENGAGE
        if robot_type == "HERO":
            return "MOVE_RIGHT", SentryState.ENGAGE
        return "MOVE_LEFT", SentryState.ENGAGE

    # R1：保命优先
    if hp_pct <= 30:
        return "RETREAT", SentryState.RETREAT

    # R2：撤退保持
    if state is SentryState.RETREAT:
        return "RETURN", SentryState.RETURN

    # R3：返航只持续一帧
    if state is SentryState.RETURN:
        return "MOVE_BASE", SentryState.PATROL

    # R4 / R5：交火状态
    if state is SentryState.ENGAGE:
        if visible:
            return engage_action()

        if len(enemy_frames) >= 2 and not enemy_frames[-2]:
            return "SCAN", SentryState.SUSPECT
        return "HOLD_FIRE", SentryState.ENGAGE

    # R6：PATROL / SUSPECT 状态下确认敌情
    if visible:
        confirmed = (len(enemy_frames) >= 2
                     and enemy_frames[-2]
                     and enemy_frames[-1])

        if confirmed:
            return engage_action()
        return "SCAN", SentryState.SUSPECT

    # R7：默认行为
    if state is SentryState.PATROL:
        return "PATROL_MOVE", SentryState.PATROL

    return "SCAN", SentryState.SUSPECT


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    left_of = {
        Facing.UP: Facing.LEFT,
        Facing.LEFT: Facing.DOWN,
        Facing.DOWN: Facing.RIGHT,
        Facing.RIGHT: Facing.UP,
    }
    right_of = {value: key for key, value in left_of.items()}

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def has_greedy_candidate():
        pos = grid.current_pos
        distance = manhattan(pos, grid.enemy_pos)

        for facing in (Facing.UP, Facing.DOWN, Facing.LEFT, Facing.RIGHT):
            dx, dy = facing.delta
            nxt = (pos[0] + dx, pos[1] + dy)

            if (not grid.is_blocked(*nxt)
                    and manhattan(nxt, grid.enemy_pos) < distance):
                return True

        return False

    def face(direction):
        order = {
            Facing.UP: 0,
            Facing.RIGHT: 1,
            Facing.DOWN: 2,
            Facing.LEFT: 3,
        }
        turns = (order[direction] - order[grid.facing]) % 4

        if turns == 3:
            grid.turn_left()
        else:
            for _ in range(turns):
                grid.turn_right()

    steps = 0
    visited = {grid.current_pos}
    wall_mode = False
    hand = "L"
    wall_steps = 0
    entry_distance = 0
    switch_limit = grid.width + grid.height

    while (steps < max_steps
           and grid.fuel > 0
           and not grid.found_enemy):

        pos = grid.current_pos

        if not wall_mode and not has_greedy_candidate():
            wall_mode = True
            hand = "L"
            wall_steps = 0
            entry_distance = manhattan(pos, grid.enemy_pos)

        if wall_mode:
            side = (left_of[grid.facing]
                    if hand == "L" else right_of[grid.facing])
            outer = (right_of[grid.facing]
                     if hand == "L" else left_of[grid.facing])

            def cell(direction):
                dx, dy = direction.delta
                return pos[0] + dx, pos[1] + dy

            if not grid.is_blocked(*cell(side)):
                face(side)
            elif grid.is_blocked(*cell(grid.facing)):
                if not grid.is_blocked(*cell(outer)):
                    face(outer)
                else:
                    grid.turn_right()
                    grid.turn_right()
        else:
            direction = next_step_toward(
                pos, grid.enemy_pos, grid.obstacles, grid.facing
            )
            face(direction)

        grid.move_forward()
        steps += 1
        visited.add(grid.current_pos)

        if wall_mode:
            wall_steps += 1

            if wall_steps > switch_limit and hand == "L":
                hand = "R"
                wall_steps = 0
            elif wall_steps > 2 * switch_limit:
                wall_mode = False
            elif (has_greedy_candidate()
                  and manhattan(grid.current_pos, grid.enemy_pos)
                  < entry_distance + 1):
                wall_mode = False

    return {
        "steps": steps,
        "collisions": grid.collision_count,
        "visited_count": len(visited),
        "found_enemy": grid.found_enemy,
        "success": grid.found_enemy,
    }


def report_to_json(stats):
    return json.dumps(stats, sort_keys=True, separators=(",", ":"))

# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------


def bfs_path_length(start, target, obstacles):
    if start == target:
        return 0

    queue = [(start, 0)]
    visited = {start}
    index = 0

    while index < len(queue):
        current, distance = queue[index]
        index += 1

        x, y = current

        for next_pos in (
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ):
            if next_pos in obstacles or next_pos in visited:
                continue

            if next_pos == target:
                return distance + 1

            visited.add(next_pos)
            queue.append((next_pos, distance + 1))

    return -1

# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
