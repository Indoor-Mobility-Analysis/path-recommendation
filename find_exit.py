#-*-coding:utf-8-*-
import numpy as np
from copy import deepcopy

class FindExit(object):

    def __init__(self, sigma_attr=20, sigma_repul=10, k_attr=100, k_repul=30):
        '''
        sigma_attr: 出口引力的标准差
        sigma_repul: 人群斥力的标准差
        k_attr: 出口引力的尺度函数
        k_repul: 人群斥力的尺度函数
        '''
        self.sigma_attr = sigma_attr
        self.sigma_repul = sigma_repul
        self.k_attr = k_attr
        self.k_repul = k_repul

    def force(self, vec, sigma, k):
        dx = vec[0]
        dy = vec[1]
        attr = float(k)/(sigma*np.sqrt(6.28)) * \
        np.exp( -(dx*dx + dy*dy) / (2.*sigma*sigma) )
        return attr
        
    def cos_sim(self, vecA, vecB):
        '''
        计算两个力的cos
        '''
        a = np.array(vecA)
        b = np.array(vecB)
        product = a.dot(b)
        norm = np.sqrt(a.dot(a)) * np.sqrt(b.dot(b)) 
        return product/norm

    def F_partial(self, vec_attr, vec_repul, sigma_repul, k_repul):
        '''
        计算斥力在引力方向的分力
        '''
        F = self.force(vec_repul, sigma_repul, k_repul) * self.cos_sim(vec_attr, vec_repul)
        return F


    def find_exit_for_one_cluster(self, cluster, cluster_list, exit_list):
        '''
        cluster: 某个人群的坐标
        cluster_list: 所有人群的坐标和density,是([x,y], density)的形式
        exit_list: 所有exit的坐标
        '''
        # from copy import copy

        # cluster_list是([x,y], density)的形式
        cluster_list1 = np.array(cluster_list)[:,0].tolist()
        # 除掉自己当前这个cluster
        cluster_list1.remove(cluster[0])
        
        F_list = []
        # 假设当前cluster至少有0.0001的density
        density = cluster[1] + 0.0001
        # 当前cluster的x,y
        cluster1 = np.array(cluster[0])
        
        # 看每个exit对于当前cluster的引力合力
        for exit in exit_list:
            exit_list_copy = deepcopy(exit_list)
            exit_list_copy.remove(exit)
            
            exit = np.array(exit)
            # 引力: exit - cluster
            vec_attr = exit - cluster1
            #当前exit的引力
            F = self.force(vec_attr, self.sigma_attr, self.k_attr)
            
            #引力,斥力合力
            for clu in cluster_list1:
                clu = np.array(clu)
                
                # 斥力: cluster - other_crowd
                vec_repul = cluster1 - clu
                
                # 因为cos_sim本身带正负号 所以是+
                repul_partial = self.F_partial(vec_attr, vec_repul, self.sigma_repul*density, self.k_repul*density)
                F += repul_partial
                
            for ex in exit_list_copy:
                ex = np.array(ex)
                
                # 其他引力: 
                vec_attr_other =  ex - cluster1
                
                # 计算分力:
                attr_partial = self.F_partial(vec_attr, vec_attr_other, self.sigma_attr, self.k_repul)
                F += attr_partial
                
            F_list.append(F)
                
        return exit_list[np.argmax(F_list)]



    def find_exit_for_all(self, cluster_list, exit_list):
        '''
        cluster_list: 所有人群的坐标
        exit_list: 所有出口的list
        '''
        exit_found = []
        for cluster in cluster_list:
            e = self.find_exit_for_one_cluster(cluster, cluster_list, exit_list)
            exit_found.append(e)
        return exit_found