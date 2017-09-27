readme.md

# 0. 思路介绍
 - 根据"人造势场法", 每个人群产生斥力, 斥力大小是人群数量和距离的函数; 每个出口产生引力, 引力大小是距离的函数. 计算每个出口对于待逃生cluster的引力合力, 选择合力最大的出口, 作为逃生目标
 - 利用A\*和改进的A\*进行路径规划, 具体分为下列6种:
  - 静态A\*, 对于每个cluster用A\*算法进行路径规划
  - 动态A\*, 每个cluster每走一步后, 都重新用A\*选择下一步
  - 静态+density A\*: 将人群和出口产生的斥力合力, 加入A\*的估值函数, 每个cluster按照改进后的算法进行路径规划
  - 动态+density A\*: 将人群和出口产生的斥力合力, 加入A\*的估值函数, 每走一步, 都重新用改进后的算法进行路径规划
  - 动态
 (可参见文件夹中path_recommendation.pptx文件)

# 1. 数据介绍
数据放在new_map文件夹中:
  - 地铁地图数据: mask_floor*.csv
  - 出口闸机数据: exit_floor*.csv
  - ground层地铁站出口数据: admiralty_gates.txt

# 2. 代码介绍
- find_exits: 为每个small cluster分配最佳出口
- density_generation: 根据small_cluster的location, density生成密度图
- path_finder: 为每个small cluster搜寻最佳路径, 可以选择多种算法
AStarStatic: 静态A\*, 可以设置weight_d来决定考虑人群密度与否 
AStarDynamic: 动态A\*, 可以设置weight_d来决定考虑人群密度与否
- grid: 将搜索地图网格化
  - node: 坐标点作为node
- a_star: A*算法
  - heuristic: 不同类别的启发函数 
  - diagnal_movement: 决定是不是可以走对角线
  - utils: 回溯父节点
- locate_preprocess: 不同数据之间坐标的转换
- process_frame: 处理某一帧图片, 将Nick原始数据中的small_clusters增加一列, 其中每个元素为路径的坐标list. 即新的small_clusters的表头含义是: x, y, rho, density, 分配好的出口, path_list 
- process_floor*: 处理某一层, 注意0层和其它层调用的函数不一样

# 3. Example
- 请见example.ipynb