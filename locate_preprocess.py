#-*-coding:utf-8-*-

def relocate_node(index_list, map_data, window_size=1):
    '''
    因为将cluster的坐标映射到maskdata, 也就是地铁地图上时, 
    会将人群映射到障碍物的区域. 所以当人群被映射的点是障碍物时,
    让其在自身周围的点, 寻找最近的左上角的点, 且是可以行走区域的点, 
    作为校正后的cluster位置.
    
    index_list: 坐标xy
    map_data: 地铁站地图
    window_size: 初始范围半径 一般默认为1, 即周围8个点
    '''
    i, j = index_list
    original = map_data[i, j]
    center = window_size/2+1
    if original != 0:
        MAX = 0
        flag = 1
        while flag == 1:
            
            area = map_data[i-window_size:i+window_size+1, j-window_size:j+window_size+1]
            flag = area.min()
            window_size +=1
        wide = area.shape[1]  
        j1 = j + area.argmin()%wide - window_size + 1
        i1 = i + area.argmin()/wide - window_size + 1
        return i1,j1
    else:
        return i,j


'''

def relocate_node(index_list, map_data, window_size=1):
    i, j = index_list
    original = map_data[i, j]
    center = window_size/2+1
    if original != 0:
        MAX = 0
        flag = 1
        while flag == 1:
            
            area = map_data[i, j-window_size:j+window_size+1]
            flag = area.min()
            window_size +=1
            #print area
        
        j1 = j + area.argmin() - window_size +1
        return i,j1
    else:
        return i,j
'''

def expand_exits(exit_list, map_data):
    '''
    mask数据中, 出口位置是落在障碍物区域的. 所以对出口位置进行填充
    认为出口位置wsize范围内也是可以行走的.
    '''
    for e in exit_list:
        i,j = e
        wsize = 2
        map_data[i, j - wsize:j + wsize + 1] = 0
    return map_data

def check_inside(ij_index, h_0=114, h_1=173):
    '''
    对于floor0来说, 闸机内部是一个封闭范围, 该函数用来检查
    是不是在闸机内部. 如果是, 则路径规划可以是先寻找最合适的闸机出口
    再寻找地铁站出口. 
    '''
    i, j = ij_index
    # 从改点向任意方向引射线, 交点个数是奇数, 则在内部; 偶数在外部.
    line = map_data[i,:j+1]
    change_point = 0
    for p in range(len(line) - 1):
        if line[p] != line[p+1]:
            change_point +=1
    print change_point
    if (change_point - 2)>0 and (change_point - 2)%2 != 0 and i > h_0 and i < h_1:
        return True
    else:
        return False  