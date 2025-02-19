### 声明

* **基于[原版](https://github.com/Mufanc/Genshin-SmartFishingRod)思路修改, 实现机制和判定方式与原版一致**

#### 改动

* 支持全屏

* 支持4k分辨率

* 无需手动配置, 脚本会自动切图初始化配置且无需用特定分辨率

* 去掉了影响性能的TK

* 修复了钓鱼过程中上钩后, 鼠标保持按下状态的bug

* 修复了鼠标事件点击的位置, 现在使用屏幕鼠标的位置

#### 使用流程:

* 管理员模式启动脚本

* 初次使用需要走下面的流程

- 1. 走到鱼点, 按下F开始钓鱼. 按下Alt + Num 1, 自动裁剪第一个图标

- 2. 开始抛竿, 等鱼上钩后 点鼠标提竿. 待浮标自动掉到最左边的时候, 按下Alt + Num2, 自动裁剪进度条位置和第二个图标.

- 3. 目录下会自动生成cfg.yml文件. 

- 4. 初始化完成, 重启脚本.

* 如果之后修改了游戏显示分辨率, 需要删掉cfg.yml重新执行初始化

#### 快捷键

* Alt + Num3 截屏

* Alt + Num4 截屏(debug模式 带辅助线) 

