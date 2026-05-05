"""
骨骼动画系统使用示例
"""
import soup3D
from pyglm import glm

# 初始化窗口
soup3D.init(1280, 720, fov=45, bg_color=(0.1, 0.1, 0.15))

# 创建相机
soup3D.camera.goto(0, 2, 5)
soup3D.camera.turn(0, 10, 0)

# 创建骨架
skeleton = soup3D.skeleton.Skeleton()

# 创建根骨骼（脊椎根部）
spine_root = soup3D.skeleton.Bone((0, 0, 0), 1.0, (0, 0, 0))
skeleton.add_bone("spine_root", spine_root)

# 创建子骨骼（头部）
head = spine_root.add_child(0.5, (0, 0, 0))
skeleton.add_bone("head", head)

# 创建手臂骨骼
arm_left = spine_root.add_child(0.8, (0, 90, 0))
skeleton.add_bone("arm_left", arm_left)

# 创建带骨骼权重的顶点数据
# 格式: ({骨骼名称: 权重, ...}, x, y, z, u, v)
skeleton_vertices = [
    ({"spine_root": 1.0}, -0.5, 0.0, 0.0, 0.0, 0.0),   # 左下
    ({"spine_root": 1.0}, 0.5, 0.0, 0.0, 1.0, 0.0),    # 右下
    ({"head": 0.8, "spine_root": 0.2}, 0.0, 1.0, 0.0, 0.5, 1.0),  # 顶点
]

# 创建骨骼绑定着色器
bone_shader = soup3D.shader.BoneBinderSP(
    base_color=soup3D.shader.MixChannel((1, 1), 0.8, 0.6, 0.4, 1.0),  # 皮肤色
    normal=(0.5, 0.5, 1.0),
    emission=(0, 0, 0),
    double_side=True,
    max_light_count=4,
    skeleton=skeleton
)

# 创建面
face = soup3D.Face("triangle_b", bone_shader, skeleton_vertices)

# 创建模型
character = soup3D.Model(0, 0, 0, face)

# 添加光源
sun = soup3D.light.Direct((-1, -1, -1), (1.0, 0.95, 0.9))
soup3D.light.add(sun)

# 显示模型
character.show()

# 骨骼动画参数
animation_time = 0.0

def update_animation():
    global animation_time
    animation_time += 0.05

    # 头部左右摆动
    head.turn(0, 0, glm.sin(animation_time) * 20)

    # 手臂前后摆动
    arm_left.turn(glm.sin(animation_time * 2) * 30, 0, 0)

    # 标记骨骼需要更新
    bone_shader.mark_bones_dirty()

# 主循环
import pygame
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # 更新骨骼动画
    update_animation()

    # 更新画布
    soup3D.update()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()