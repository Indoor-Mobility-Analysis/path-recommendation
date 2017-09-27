#-*-encoding:utf-8-*-
from diagonal_movement import DiagonalMovement
from grid import Grid
from a_star import AStarFinder
from density_generation import DMap
import pandas as pd
from copy import copy
import numpy as np
from scipy.ndimage import filters




def relocate_paths_xy(cleaned_paths_sep):
    
    for i in range(len(cleaned_paths_sep)):
        path = cleaned_paths_sep[i]
        for j in range(len(path)):
            cleaned_paths_sep[i][j] = (path[j][0], 230 - path[j][1])
    return cleaned_paths_sep

def get_gradient(show_data):
    '''
    计算density map的梯度, 可以是录路径规划的一项
    '''

    imx = np.zeros(show_data.shape)
    filters.sobel(show_data, 1, imx)

    imy = np.zeros(show_data.shape)
    filters.sobel(show_data, 0 , imy)
    
    m = DMap()
    magnitude = m.normlize(np.sqrt(imx**2 + imy**2))

    return magnitude

class AStarStatic(object):
    
    def __init__(self, map_data=None, density=None, gradient=False):
        '''
        map_data: 地铁站的地图数据, 即mask data
        density: 根据small_clusters和exits得到的密度图
        gradient: 是否考虑density的梯度来进行路径规划
        '''

        '''
        always: 总可以走对角线, 不管有没有障碍物
        one_obstacle: 周围的格子对多有一个是障碍物, 则可以走
        never: 不能走对角线
        no_obstacle: 周围的格子没有障碍物, 才可以走对角线
        '''
        self.Diagonal = {'always':DiagonalMovement.always, \
        'one_obstacle': DiagonalMovement.if_at_most_one_obstacle,\
        'never':DiagonalMovement.never, \
        'no_obstacle':DiagonalMovement.only_when_no_obstacle}

        self.map_data = map_data
        
        if gradient:
            self.show_data = - get_gradient(density)
        else:
            self.show_data = density

    def find_paths(self, start_list, end_list, diagonal='no_obstacle', weight_d=1, weight_h=1, ):
        '''
        start_list: 所有small_clusters的初始位置
        end_list: 给small_clusters分配好的exits位置
        diagonal: 是否考虑走对角线, 
        weight_d: density map的权重
        weight_h: 计算离end距离的启发函数的权重
        '''
        diag = self.Diagonal[diagnoal]

        finder = AStarFinder(diagonal_movement=diag, weight=weight_h)
  

        # start_end是每个small_cluster的位置, 以及对应的exit坐标
        # [((197, 9), (162, 16)), ((119, 41), (146, 37)),]
        start_end = zip(start_list, end_list)

        # 利用a-star来寻找路径
        paths = []
        paths_sep = []
        for s, end_node in start_end:
            grid = Grid(matrix=self.map_data.tolist(), density=self.show_data*weight_d)
            start = grid.node(s[1], s[0])
            end = grid.node(end_node[1], end_node[0])
            
            path, runs = finder.find_path(start, end, grid)
        #     print len(path)
            paths.extend(path)
            paths_sep.append(path)
        return paths_sep


class AStarDynamic(object):
    
    def __init__(self, map_data=None, small_cluster=None, exit_list=None):
        self.Diagonal = {'always':DiagonalMovement.always, \
        'one_obstacle': DiagonalMovement.if_at_most_one_obstacle,\
        'never':DiagonalMovement.never, \
        'no_obstacle':DiagonalMovement.only_when_no_obstacle}

        self.map_data = map_data
        self.small_cluster = small_cluster.copy()
        self.exit_list = exit_list


    

    def find_paths(self, start_list, end_list, diagnoal='no_obstacle',weight_d=1, weight_h=1, \
                   print_or_not=False, gradient=False):
        '''
        print_or_not: 是否打印计算时间等细节
        '''
            
        diag = self.Diagonal[diagnoal]
        finder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle, weight=weight_h, )
        
        start_end = zip(start_list, end_list)

        # 创建密度图
        M = DMap(sigma=10)

        # density_map这个函数是按照small_cluster的xy写的
        # x是0-50,y是0-230
        crowd_density = M.density_map(self.map_data.shape, self.small_cluster, crowd=True)

        # exits_list的x大,y小,所以xy坐标需要换一下位置, 
        exits_density = M.density_map(self.map_data.shape, pd.DataFrame(self.exit_list[:,[1,0]]), sigma=5)
        show_data = crowd_density-exits_density
        
        if gradient:
            show_data = - get_gradient(show_data)
            # print 'gradient'
        
        small_cluster1 = self.small_cluster

        # 开始while循环
        PATHS = []
        PATHS.append(start_list)
        from datetime import datetime

        t1 = datetime.now()

        j = 0

        while start_list != end_list:
            if j%10 == 0 and print_or_not:
                print j

            flag = 0 
            paths = []
            paths_sep = []
            
            for s, end_node in start_end:
                
                if s == end_node:
                    path = [(s[1],s[0]), (end_node[1], end_node[0])]
                    flag = 1
                    
                else:
                    grid = Grid(matrix=self.map_data.tolist(), density=show_data*weight_d)
                    start = grid.node(s[1], s[0])
                    end = grid.node(end_node[1], end_node[0])

                    path, runs = finder.find_path(start, end, grid)
                #     print len(path)
                paths.extend(path)
                paths_sep.append(path)

            #----------------
            start_list = [i[1] for i in paths_sep]

            # 更新small cluster
            small_cluster1[[0,1]] = pd.DataFrame(start_list)

            # 更新start_list
            start_list = [(i[1], i[0]) for i in start_list]
            PATHS.append(start_list)

            # 更新start_end
            start_end = zip(start_list, end_list)

            # ------------------
            # 更新density map
            drops = []
            # 如果有点已经到达终点, 那么就不要再产生density
            if flag == 1:
                ind = 0
                
                for s, e in start_end:
                    if s == e:
                        drops.append(ind)
                    ind +=1
            
            crowd_density = M.density_map(self.map_data.shape, small_cluster1.drop(drops, axis=0), crowd=True)
            
            # 为了好看..完全可以删掉
            crowd_density2 = M.density_map(self.map_data.shape, small_cluster1, crowd=True)
            # exits_density = M.density_map(map_data.shape, pd.DataFrame(exit_list[:,[1,0]]), sigma=5)

            # 更新 show_data
            show_data = crowd_density-exits_density
            
            # gradient way
            if gradient:
                show_data = - get_gradient(show_data)
                # print 'gradient'
            
            j+=1

        if print_or_not:
            print datetime.now() - t1

        PATHS = pd.DataFrame(PATHS).T

        # 处理成path_list, 
        paths_sep = []
        for l in range(len(PATHS)):
            p = [(i[1], i[0]) for i in list(PATHS.iloc[l])]
            paths_sep.append(p)

        return paths_sep
    
    def clean_paths_sep(self, paths_sep):
        for i in range(len(paths_sep)):
            p = paths_sep[i]
            for j in range(len(p)-1):
                if p[j] == p[j+1]:
                    paths_sep[i] = paths_sep[i][:j+1]
        return paths_sep
