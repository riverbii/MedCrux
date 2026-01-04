"""
测试12个钟点方向的坐标计算

QA测试用例：验证所有12个钟点方向的位置是否正确
"""
import math
import pytest


def calculate_clock_position(clock_position: str, breast_side: str = "left", distance_cm: float = 3.0):
    """
    计算钟点位置的坐标（用于测试）

    Args:
        clock_position: 钟点位置（如"12点"、"3点"等）
        breast_side: 乳腺侧（"left"或"right"）
        distance_cm: 距乳头距离（cm）

    Returns:
        (x_pos, y_pos): 坐标
    """
    # 从钟点位置计算角度（12点为90度，顺时针递减）
    clock_angle = 90.0  # 默认12点方向（上方）
    if "12点" in clock_position:
        clock_angle = 90.0
    elif "1点" in clock_position:
        clock_angle = 60.0
    elif "2点" in clock_position:
        clock_angle = 30.0
    elif "3点" in clock_position:
        clock_angle = 0.0
    elif "4点" in clock_position:
        clock_angle = -30.0
    elif "5点" in clock_position:
        clock_angle = -60.0
    elif "6点" in clock_position:
        clock_angle = -90.0
    elif "7点" in clock_position:
        clock_angle = -120.0
    elif "8点" in clock_position:
        clock_angle = -150.0
    elif "9点" in clock_position:
        clock_angle = 180.0
    elif "10点" in clock_position:
        clock_angle = 150.0
    elif "11点" in clock_position:
        clock_angle = 120.0

    # 计算半径
    actual_breast_radius = 7.5  # cm
    diagram_radius = 0.85
    ratio = min(distance_cm / actual_breast_radius, 0.9)
    r = diagram_radius * ratio

    # 转换为弧度
    angle_rad = math.radians(clock_angle)

    # 计算坐标
    x_pos_base = r * math.cos(angle_rad)
    y_pos = r * math.sin(angle_rad)

    # 对于右乳，镜像x坐标
    if breast_side == "left":
        x_pos = x_pos_base
    else:  # right
        x_pos = -x_pos_base

    return (x_pos, y_pos)


class TestClockPositions:
    """测试12个钟点方向"""

    def test_12_oclock_left(self):
        """测试左乳12点（上方）"""
        x, y = calculate_clock_position("12点", "left")
        assert abs(x) < 0.01, "12点应该在正上方，x应该接近0"
        assert y > 0, "12点应该在正上方，y应该为正"

    def test_3_oclock_left(self):
        """测试左乳3点（右侧）"""
        x, y = calculate_clock_position("3点", "left")
        assert x > 0, "3点应该在右侧，x应该为正"
        assert abs(y) < 0.01, "3点应该在正右侧，y应该接近0"

    def test_6_oclock_left(self):
        """测试左乳6点（下方）"""
        x, y = calculate_clock_position("6点", "left")
        assert abs(x) < 0.01, "6点应该在正下方，x应该接近0"
        assert y < 0, "6点应该在正下方，y应该为负"

    def test_9_oclock_left(self):
        """测试左乳9点（左侧）"""
        x, y = calculate_clock_position("9点", "left")
        assert x < 0, "9点应该在左侧，x应该为负"
        assert abs(y) < 0.01, "9点应该在正左侧，y应该接近0"

    def test_11_oclock_left(self):
        """测试左乳11点（左上方）"""
        x, y = calculate_clock_position("11点", "left")
        assert x < 0, "11点应该在左上方，x应该为负"
        assert y > 0, "11点应该在左上方，y应该为正"
        # 11点应该在12点和9点之间，所以x和y的绝对值应该相近
        assert abs(abs(x) - abs(y)) < 0.2, "11点的x和y绝对值应该相近"

    def test_1_oclock_left(self):
        """测试左乳1点（右上方）"""
        x, y = calculate_clock_position("1点", "left")
        assert x > 0, "1点应该在右上方，x应该为正"
        assert y > 0, "1点应该在右上方，y应该为正"

    def test_12_oclock_right(self):
        """测试右乳12点（上方）"""
        x, y = calculate_clock_position("12点", "right")
        assert abs(x) < 0.01, "12点应该在正上方，x应该接近0"
        assert y > 0, "12点应该在正上方，y应该为正"

    def test_3_oclock_right(self):
        """测试右乳3点（右侧）"""
        x, y = calculate_clock_position("3点", "right")
        assert x > 0, "3点应该在右侧，x应该为正（右乳镜像后）"
        assert abs(y) < 0.01, "3点应该在正右侧，y应该接近0"

    def test_9_oclock_right(self):
        """测试右乳9点（左侧）"""
        x, y = calculate_clock_position("9点", "right")
        assert x < 0, "9点应该在左侧，x应该为负（右乳镜像后）"
        assert abs(y) < 0.01, "9点应该在正左侧，y应该接近0"

    def test_11_oclock_right(self):
        """测试右乳11点（左上方）"""
        x, y = calculate_clock_position("11点", "right")
        assert x < 0, "11点应该在左上方，x应该为负（右乳镜像后）"
        assert y > 0, "11点应该在左上方，y应该为正"

    def test_all_clock_positions_left(self):
        """测试左乳所有12个钟点"""
        clock_positions = ["12点", "1点", "2点", "3点", "4点", "5点", "6点", "7点", "8点", "9点", "10点", "11点"]
        for clock_pos in clock_positions:
            x, y = calculate_clock_position(clock_pos, "left")
            # 验证坐标在合理范围内
            assert -1.0 < x < 1.0, f"{clock_pos}的x坐标应该在合理范围内"
            assert -1.0 < y < 1.0, f"{clock_pos}的y坐标应该在合理范围内"

    def test_all_clock_positions_right(self):
        """测试右乳所有12个钟点"""
        clock_positions = ["12点", "1点", "2点", "3点", "4点", "5点", "6点", "7点", "8点", "9点", "10点", "11点"]
        for clock_pos in clock_positions:
            x, y = calculate_clock_position(clock_pos, "right")
            # 验证坐标在合理范围内
            assert -1.0 < x < 1.0, f"{clock_pos}的x坐标应该在合理范围内"
            assert -1.0 < y < 1.0, f"{clock_pos}的y坐标应该在合理范围内"

    def test_symmetry_between_left_and_right(self):
        """测试左右乳的对称性"""
        clock_positions = ["12点", "3点", "6点", "9点"]
        for clock_pos in clock_positions:
            x_left, y_left = calculate_clock_position(clock_pos, "left")
            x_right, y_right = calculate_clock_position(clock_pos, "right")
            
            # 对于对称的钟点（12点、6点），y应该相同，x应该相反
            if clock_pos in ["12点", "6点"]:
                assert abs(y_left - y_right) < 0.01, f"{clock_pos}的y坐标应该相同"
                assert abs(x_left + x_right) < 0.01, f"{clock_pos}的x坐标应该相反"
            # 对于3点和9点，镜像后应该交换位置
            elif clock_pos == "3点":
                assert abs(x_left - x_right) < 0.01, "3点镜像后x应该相同"
            elif clock_pos == "9点":
                assert abs(x_left - x_right) < 0.01, "9点镜像后x应该相同"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

