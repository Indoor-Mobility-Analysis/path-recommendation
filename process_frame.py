#-*-coding:utf-8-*-

# from pymongo import MongoClient
import pandas as pd
import json
import codecs
import numpy as np
from find_exit import FindExit
from density_generation import DMap
from matplotlib import pyplot as plt
from path_finder import  AStarDynamic
from locate_preprocess import relocate_node, expand_exits
from datetime import datetime

class FrameProcess(object):

    def __init__(self, d_sigma=20, k_attr=100, k_repul=5, sigma_attr=50, sigma_repul=50,weight_d=1, floor=0):
        '''
        d_sigma: 生成出口density的标准差, 影响路径规划
        k_attr: 出口引力的尺度函数, 影响出口选择
        k_repul: 人群斥力的尺度函数, 影响出口选择
        sigma_attr: 出口引力的标准差, 影响出口选择
        '''
        self.d_sigma = d_sigma
        self.k_attr = k_attr
        self.k_repul = k_repul
        self.sigma_attr = sigma_attr
        self.sigma_repul = sigma_repul
        self.weight_d = weight_d
        if floor == 0:
            self.dic = {'[101, 11]': u'gate_2', '[11, 15]': u'gate_0', '[201, 4]': u'gate_3', \
                        '[213, 3]': u'gate_4', '[73, 35]': u'gate_1'}
        elif floor == -1:
            self.dic = {'[120, 22]': u'gate_3', '[120, 25]': u'gate_2', '[170, 22]': u'gate_0',\
                        '[170, 25]': u'gate_1'}
        elif floor == -2:
            self.dic = {'[150, 22]': u'gate_0', '[87, 30]': u'gate_1'}


    def process_one_frame_floor0(self, frame_data, map_path, exits_path, gates_path, print_or_not=False):
        '''
        这个函数只用于处理floor0

        frame_data: pymongo里面的一条记录
        map_path: mask data的路径(含文件名)
        exits_path: exits的路径
        gates_path: 地铁站出口的路径
        print_or_not: 是否打印路径规划的时间细节
        '''

#        # self.frame_data = frame_data
#        if map_path == None:
#            map_path = './new_map/mask_floor.csv'
#        if exits_path == None:
#            exits_path = '../map_data/exit_floor0.csv'
#        if gates_path == None:
#            gates_path = './new_map/admiralty_gates.txt'

        # get map_data
        # map_data = pd.read_csv('../map_data/mask_floor0.csv', header=None)
        map_data = pd.read_csv(map_path, header=None, sep=' ')
        map_data = - (np.array(map_data).astype(int) - 1)


        # get exit_list
        # 注意这里的xy坐标并不是矩阵的index, 后面要进行转换.
        exits = pd.read_csv(exits_path, header=None, )
        exits = exits.T

        # 坐标-->索引
        exits[0] = exits[0].astype(float)
        # '''看这里'''
        exits[1] = 230 - exits[1].astype(float)

        exit_list = np.array(exits.ix[:,[1,0]]) #令0-230的在前面

        map_data = expand_exits(exit_list.astype(int), map_data)
        self.map_data = map_data

        # gate的坐标不要转换.
        gates = pd.read_table(gates_path, header=None, sep=' ')[[1,0]]

        gates.columns = range(gates.shape[1])

        exits_all = pd.concat([gates, pd.DataFrame(exit_list)], axis=0)[[1,0]]
        exits_all.index = range(exits_all.shape[0])
        exits_all.columns = range(exits_all.shape[1])

        self.exits_all = exits_all

        try:
            # get cluster_list
            # 注意这里的xy坐标并不是矩阵的index, 后面要进行转换.
            small_cluster = frame_data['small_clusters']

            small_cluster = pd.DataFrame(small_cluster)
            small_cluster = small_cluster[small_cluster[4] > 0]
            
            bigger_index = small_cluster[small_cluster[4] > 0].index
            
            small_cluster.index = range(len(small_cluster))

            # 坐标-->索引
            small_cluster[1] = 230 - small_cluster[1]
            
            self.small_cluster = small_cluster

            cluster_list = np.array(small_cluster[[1, 0]]).astype(int)
            cl = zip(cluster_list.tolist(), small_cluster[4])  # cl = [([197, 9], 1.0),...,([],1.0)]

            # 创建初始状态密度图
            M = DMap(sigma=10)
            # density_map这个函数是按照small_cluster的xy写的
            # x是0-50,y是0-230
            crowd_density = M.density_map(map_data.shape, small_cluster, crowd=True)

            # exits_list的x大,y小,所以xy坐标需要换一下位置,
            # exits_density = M.density_map(map_data.shape, pd.DataFrame(exit_list[:,[1,0]]), sigma=5)
            d_sigma = self.d_sigma
            exits_density = M.density_map(map_data.shape, exits_all[[1, 0]], sigma=d_sigma)


            # find exits for each cluster
            k_attr = self.k_attr
            k_repul = self.k_repul
            sigma_attr = self.sigma_attr
            sigma_repul = self.sigma_repul
            
            exit_finder = FindExit(k_attr=k_attr, k_repul=k_repul, sigma_attr=sigma_attr, sigma_repul=sigma_repul)
            exits_matched = pd.DataFrame(exit_finder.find_exit_for_all(cl, np.array(gates).tolist()))

            exits_matched = pd.concat([small_cluster, exits_matched], axis=1, ignore_index=True)
            
            
            # get the label of gates matched
            xx =np.array(exit_finder.find_exit_for_all(cl, np.array(gates).tolist())).astype(int).tolist()
            xx = [str(i) for i in xx]

            gates_name_matched = [self.dic[i] for i in xx]
            
            

            start_list1 = [relocate_node(tuple(small_cluster[[1, 0]].astype(int).iloc[i]), \
                                         map_data, 1) for i in range(len(small_cluster))]
            # end_list1 = [tuple(exits_matched[[6,7]].astype(int).iloc[i]+2) for i in range(len(exits_matched))]
            end_list1 = [relocate_node(tuple(exits_matched[[6, 7]].astype(int).iloc[i]), \
                                       map_data, 1) for i in range(len(exits_matched))]

            start_end = zip(start_list1, end_list1)

            # small_cluster2 = small_cluster.copy()
            finder = AStarDynamic(map_data, small_cluster, exit_list, )
            
            flag_p = print_or_not
            
            weight_d = self.weight_d

            paths_sep = finder.find_paths(start_list1, end_list1, print_or_not=flag_p, weight_d=weight_d, )

            paths_sep = finder.clean_paths_sep(paths_sep)

            self.paths_sep = paths_sep



            show_data = crowd_density - exits_density
            self.masked_data = np.ma.masked_where(map_data == 1, show_data)


            # 如何写入数据库
            paths_list = [[path] for path in paths_sep]
            paths_list1 = []
            for li in paths_list:
                li = np.array(li).T
                li[1] = 230 - li[1]
                paths_list1.append(li.T.tolist())
            paths_list = paths_list1

            paths_df = pd.DataFrame(paths_list)
            
            paths_df.index = bigger_index
            
            small_cluster = pd.DataFrame(frame_data['small_clusters'])
            small_cluster[5] = u'None'
            small_cluster.ix[bigger_index,5] = gates_name_matched
            new_small_clusters = pd.concat([ small_cluster, paths_df], axis=1).fillna(u'None')
            new_small_clusters[7] = small_cluster[4]*9
            
            new_small_clusters = np.array(new_small_clusters).tolist()
            
            # collection.update_one({u'_id':record[u'_id']}, {'$set':{'small_clusters':new_small_clusters}})

            return new_small_clusters

        except Exception, e:

            f = open('wrong_log.txt', 'aw')
            f.write(str(datetime.now())[:-7] + ', ' + str(frame_data['_id']) + ', ' + str(e) + ',\n')
            f.close()
            print str(frame_data['_id']), str(e)
            return []

    def plot_results(self,):
        '''
        将density map. 规划好的路径. 一并plot出来.
        '''

        small_cluster = self.small_cluster
        exits_all = self.exits_all

        # _____________________________________________________________
        plt.rcParams['figure.figsize'] = (10, 10)

        plt.scatter(small_cluster[0], small_cluster[1], )

        plt.scatter(exits_all[0], exits_all[1])

        # 画出路径
        for p in self.paths_sep:
            try:
                p = np.array(p).T
                plt.plot(p[0], p[1], c='w', linestyle=':')
            except:
                print 'plt bug'

        plt.imshow(self.map_data, cmap='PiYG', alpha=0.55)
        plt.imshow(self.masked_data, interpolation='none', alpha=0.8)

        # plt.axis('off')
        plt.show()

    def process_one_frame_floorX(self, frame_data, map_path=None, exits_path=None, print_or_not=False):
        '''
        这个函数用来处理除了floor0以外的数据
        '''
        # self.frame_data = frame_data
        if map_path == None:
            map_path = './new_map/mask_floor-1.csv'
        if exits_path == None:
            exits_path = '../map_data/exit_floor-1.csv'
        

        # get map_data
        # map_data = pd.read_csv('../map_data/mask_floor0.csv', header=None)
        map_data = pd.read_csv(map_path, header=None, sep=' ')
        map_data = - (np.array(map_data).astype(int) - 1)


        # get exit_list
        # 注意这里的xy坐标并不是矩阵的index, 后面要进行转换.
        exits = pd.read_csv(exits_path, header=None, )
        exits = exits.T

        # 坐标-->索引
        exits[0] = exits[0].astype(float)
        # '''看这里'''
        exits[1] = 230 - exits[1].astype(float)

        exit_list = np.array(exits.ix[:,[1,0]]) #令0-230的在前面

        map_data = expand_exits(exit_list.astype(int), map_data)
        self.map_data = map_data

        
        exits_all = pd.DataFrame(exit_list)[[1,0]]
        # exits_all.index = range(exits_all.shape[0])
        exits_all.columns = range(exits_all.shape[1])

        self.exits_all = exits_all

        try:
            # get cluster_list
            # 注意这里的xy坐标并不是矩阵的index, 后面要进行转换.
            small_cluster = frame_data['small_clusters']

            small_cluster = pd.DataFrame(small_cluster)
            small_cluster = small_cluster[small_cluster[4] > 0]
            
            bigger_index = small_cluster[small_cluster[4] > 0].index
            
            small_cluster.index = range(len(small_cluster))

            # 坐标-->索引
            small_cluster[1] = 230 - small_cluster[1]

            self.small_cluster = small_cluster

            cluster_list = np.array(small_cluster[[1, 0]]).astype(int)
            cl = zip(cluster_list.tolist(), small_cluster[4])  # cl = [([197, 9], 1.0),...,([],1.0)]

            # 创建初始状态密度图
            M = DMap(sigma=10)
            # density_map这个函数是按照small_cluster的xy写的
            # x是0-50,y是0-230
            crowd_density = M.density_map(map_data.shape, small_cluster, crowd=True)

            # exits_list的x大,y小,所以xy坐标需要换一下位置,
            # exits_density = M.density_map(map_data.shape, pd.DataFrame(exit_list[:,[1,0]]), sigma=5)
            d_sigma = self.d_sigma
            exits_density = M.density_map(map_data.shape, exits_all[[1, 0]], sigma=d_sigma)


            # find exits for each cluster
            k_attr = self.k_attr
            k_repul = self.k_repul
            sigma_attr = self.sigma_attr
            sigma_repul = self.sigma_repul

            exit_finder = FindExit(k_attr=k_attr, k_repul=k_repul, sigma_attr=sigma_attr, sigma_repul=sigma_repul)
            
            exits_cache = exit_finder.find_exit_for_all(cl, np.array(exit_list).tolist())
            
            exits_matched = pd.DataFrame(exits_cache)

            exits_matched = pd.concat([small_cluster, exits_matched], axis=1, ignore_index=True)
            
            # get the label of gates matched
            xx =np.array(exits_cache).astype(int).tolist()
            xx = [str(i) for i in xx]

            gates_name_matched = [self.dic[i] for i in xx]            
            
            

            start_list1 = [relocate_node(tuple(small_cluster[[1, 0]].astype(int).iloc[i]), \
                                         map_data, 1) for i in range(len(small_cluster))]
            # end_list1 = [tuple(exits_matched[[6,7]].astype(int).iloc[i]+2) for i in range(len(exits_matched))]
            end_list1 = [relocate_node(tuple(exits_matched[[6, 7]].astype(int).iloc[i]), \
                                       map_data, 1) for i in range(len(exits_matched))]

            start_end = zip(start_list1, end_list1)

            # small_cluster2 = small_cluster.copy()
            finder = AStarDynamic(map_data, small_cluster, exit_list, )

            flag_p = print_or_not

            weight_d = self.weight_d

            paths_sep = finder.find_paths(start_list1, end_list1, print_or_not=flag_p, weight_d=weight_d, )

            paths_sep = finder.clean_paths_sep(paths_sep)

            self.paths_sep = paths_sep



            show_data = crowd_density - exits_density
            self.masked_data = np.ma.masked_where(map_data == 1, show_data)


            # 如何写入数据库
            paths_list = [[path] for path in paths_sep]
            paths_list1 = []
            for li in paths_list:
                li = np.array(li).T
                li[1] = 230 - li[1]
                paths_list1.append(li.T.tolist())
            paths_list = paths_list1

            paths_df = pd.DataFrame(paths_list)
            paths_df.index = bigger_index
            
            small_cluster = pd.DataFrame(frame_data['small_clusters'])
            small_cluster[5] = u'None'
            small_cluster.ix[bigger_index,5] = gates_name_matched
            new_small_clusters = pd.concat([ small_cluster, paths_df], axis=1).fillna(u'None')
            new_small_clusters[7] = small_cluster[4]*9
            
            new_small_clusters = np.array(new_small_clusters).tolist()
            
            # collection.update_one({u'_id':record[u'_id']}, {'$set':{'small_clusters':new_small_clusters}})

            return new_small_clusters

        except Exception, e:

            f = open('wrong_log.txt', 'aw')
            f.write(str(datetime.now())[:-7] + ', ' + str(frame_data['_id']) + ', ' + str(e) + ',\n')
            f.close()
            print str(frame_data['_id']), str(e)
            return []
