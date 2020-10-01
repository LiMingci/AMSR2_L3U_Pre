# Name:    AMSR2_L3U_Pre.py
# Purpose: clip AMSR2 L3 base border
# Created:      LiMingci at 2020.08.15
# Modification:
import numpy as np
import h5py
from osgeo import gdal
from nansat import NSR
from nansat.vrt import VRT


class AMSR2L3UPre(object):
    def __init__(self, filename):
        self.filename = filename
        with h5py.File(filename, 'r') as f:
            self.nh_89h = f['HDFEOS']['GRIDS']['NpPolarGrid06km']['Data Fields']['SI_06km_NH_89H_DAY'][:]
            self.nh_89v = f['HDFEOS']['GRIDS']['NpPolarGrid06km']['Data Fields']['SI_06km_NH_89V_DAY'][:]
            self.nh_lat = f['HDFEOS']['GRIDS']['NpPolarGrid06km']['lat'][:]
            self.nh_lon = f['HDFEOS']['GRIDS']['NpPolarGrid06km']['lon'][:]

            self.lu_x = -3850000.0
            self.lu_y = 5850000.0
            self.gsd = 6250.0
            self.data_shape = self.nh_89h.shape


    def proj_to_nsidc_sea_ice_stere_n(self, x, y, inverse=False):
        '''
        获得NSIDC Sea Ice Polar Stereographic投影下的坐标
        :param x: 1D array -->lon
        :param y: 1D array -->lat
        :param iinverse:
        :return:
        '''
        # WGS84
        srs_src = NSR(4326)
        # NSIDC Sea Ice Polar Stereographic
        srs_dst = NSR(3411)
        src_points = (x, y)
        if inverse:
            dst_point = VRT.transform_coordinates(srs_dst, src_points, srs_src)
        else:
            dst_point = VRT.transform_coordinates(srs_src, src_points, srs_dst)
        return dst_point


    def reproj_roi(self, out_path, lonw, lone, lats, latn):
        '''
        根据给定的经纬度方位裁剪AMSR2 L3 数据
        :param out_path:
        :param lonw:
        :param lone:
        :param lats:
        :param latn:
        :return:
        '''
        corner_lon = [lonw, lone, lone, lonw]
        corner_lat = [lats, lats, latn, latn]
        corner_xy = self.proj_to_nsidc_sea_ice_stere_n(corner_lon, corner_lat)
        min_x = corner_xy[0].min()
        max_x = corner_xy[0].max()
        min_y = corner_xy[1].min()
        max_y = corner_xy[1].max()
        start_x = min_x - self.lu_x
        end_x = max_x - self.lu_x
        start_x_pixel = int(start_x / self.gsd)
        end_x_pixel = int(np.ceil(end_x / self.gsd))
        if start_x_pixel < 0:
            start_x_pixel = 0
        if end_x_pixel >= self.data_shape[1]:
            end_x_pixel = self.data_shape[1] - 1
        start_y = self.lu_y - max_y
        end_y = self.lu_y - min_y
        start_y_pixel = int(start_y / self.gsd)
        end_y_pixel = int(np.ceil(end_y / self.gsd))
        if start_y_pixel < 0:
            start_y_pixel = 0
        if end_y_pixel >= self.data_shape[0]:
            end_y_pixel = self.data_shape[0] - 1

        # 获得区域内的亮温
        sub_nh_89h = self.nh_89h[start_y_pixel:end_y_pixel, start_x_pixel:end_x_pixel].copy()
        sub_nh_89v = self.nh_89v[start_y_pixel:end_y_pixel, start_x_pixel:end_x_pixel].copy()
        origin_x = start_x_pixel * self.gsd + self.lu_x
        origin_y = self.lu_y - start_y_pixel * self.gsd

        file_format = 'GTiff'
        driver = gdal.GetDriverByName(file_format)
        dst_ds = driver.Create(out_path, xsize=sub_nh_89h.shape[1], ysize=sub_nh_89h.shape[0],
                               bands=2, eType=gdal.GDT_Int32)
        srs = NSR(3411)
        dst_ds.SetProjection(srs.ExportToWkt())
        dst_ds.SetGeoTransform([origin_x, self.gsd, 0, origin_y, 0, -self.gsd])

        band1 = dst_ds.GetRasterBand(1)
        band1.WriteArray(sub_nh_89h)
        band2 = dst_ds.GetRasterBand(2)
        band2.WriteArray(sub_nh_89v)
        dst_ds = None

