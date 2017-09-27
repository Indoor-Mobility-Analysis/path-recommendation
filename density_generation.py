#-*-coding:utf-8-*-
import numpy as np

class DMap(object):
    '''
    以每个cluster的坐标为圆心, 以高斯核构建density map.
    crowd的density可以理解为, 由于人多给路人造成的压力, 所以不愿意往这边走
    exit的density可以理解为, 由于是出口, 给路人造成的吸引力.
    cluster的density map考虑人数/密度, 人数越多, 半径越大, 尺度因子越大
    exit的density的半径和尺度因子是常数.
    若density map的范围内有障碍物边界(如墙壁), 则reshape density map的形状.
    '''

    def __init__(self,sigma=10):
        self.k = 1
        self.sigma = sigma


    def gauss2D(self, shape,sigma):
        '''
        构建符合高斯分布的矩阵
        '''
        m,n = [(ss-1.)/2. for ss in shape]
        y,x = np.ogrid[-m:m+1,-n:n+1]
        h = np.exp( -(x*x + y*y) / (2.*sigma*sigma) )
        h[ h < np.finfo(h.dtype).eps*h.max() ] = 0
#         sumh = h.sum()
#         if sumh != 0:
#             h /= sumh
        a = h*np.log2(self.k+1)
        #print a
        return a

    def normlize(self, density_map):
        max1 = density_map.max()
        min1 = density_map.min()
        if max1 - min1 <= 1e-5:
            return density_map
        else:
            return (density_map - min1) / (max1 - min1)
    
    
    def density_map(self, shape, small_cluster, crowd=False, sigma=False):
        '''
        将每个cluster的位置, 按照地图, 生成整个地图的density map
        '''

        if not sigma:
            sigma=self.sigma

        h, w = shape
        zos = np.zeros([h, w])

        for i in range(len(small_cluster)):

            if crowd:
                self.k = small_cluster.iloc[i][4] 

            vv = sigma*np.log2(self.k+1)
            #print i
            #print 'sigma:', vv

            vv1 = vv*3 # because of the distribution 99% in this area
            radi = int(round(vv1/2.0),)
 
            
            kernel = self.gauss2D(shape=(radi*2,radi*2), sigma=vv)

            m = int(small_cluster.iloc[i][1])# respond to the width of image
            n = int(small_cluster.iloc[i][0])# respond to the hight of image
            

            try:
                zos[m - radi:m + radi, n-radi:n+radi] += kernel

            except:
                try:
                    if (m - radi<0) and (n -radi < 0):
                        kernel = self.gauss2D(shape=zos[0:m + radi, 0:n+radi].shape, sigma=vv)
                        zos[0:m + radi, 0:n+radi] += kernel
                        #kernel[radi-m:, radi-n: ]

                    elif (m + radi>h-1) and (n +radi >w-1):
                        kernel = self.gauss2D(shape=zos[m-radi:h, n-radi:w].shape, sigma=vv)
                        zos[m-radi:h, n-radi:w] += kernel
                        #kernel[:251-m-radi, :251-n-radi]

                    elif (m - radi<0) and(n +radi >w-1):
                        kernel = self.gauss2D(shape=zos[0:m + radi, n-radi:h].shape, sigma=vv)
                        zos[0:m + radi, n-radi:w] += kernel
                        #kernel[radi-m-1:, :251-n-radi]

                    elif (m + radi>h-1) and (n - radi <0):
                        kernel = self.gauss2D(shape=zos[m-radi:h, 0:n+radi].shape, sigma=vv)
                        zos[m-radi:h, 0:n+radi] += kernel
                        #kernel[:251-m-radi, radi-n:] 

                    elif n -radi < 0:
                        kernel = self.gauss2D(shape=zos[m-radi:m+radi, 0:n+radi].shape, sigma=vv)
                        zos[m-radi:m+radi, 0:n+radi] += kernel

                    elif n + radi >w-1:
                        kernel = self.gauss2D(shape=zos[m-radi:m+radi, n-radi:w].shape, sigma=vv)
                        zos[m-radi:m+radi, n-radi:w] += kernel

                    elif m -radi < 0:
                        kernel = self.gauss2D(shape=zos[0:m + radi,n-radi:n+radi].shape, sigma=vv)
                        zos[0:m + radi,n-radi:n+radi] += kernel

                    elif m + radi > h-1:
                        kernel = self.gauss2D(shape=zos[m-radi:h, n-radi:n+radi,].shape, sigma=vv)
                        zos[m-radi:h, n-radi:n+radi,] += kernel

                except:
                    print 'BUG'

        return self.normlize(zos)
    
