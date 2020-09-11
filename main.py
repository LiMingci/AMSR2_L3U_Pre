import os
import glob
from multiprocessing import Pool
import AMSR2L3UPre


def batch_reproj_roi(amsr2_path):
    out_path = "%s_Fram.tiff" % os.path.splitext(amsr2_path)[0]
    amsr2_pre = AMSR2L3UPre.AMSR2L3UPre(amsr2_path)
    amsr2_pre.reproj_roi(out_path, lonw=-20.0, lone=20.0, lats=77.0, latn=81.0)
    print(os.path.basename(out_path))
    pass


if __name__ == "__main__":
    # amsr2_path = "E:/SeaIceDrift/data/AMSR2/2018/AMSR_U2_L3_SeaIce6km_B04_20180102.he5"
    # out_path = "E:/SeaIceDrift/data/AMSR2/2018/AMSR_U2_L3_SeaIce6km_B04_20180102_New.tiff"

    file_list = glob.glob("E:/SeaIceDrift/data/AMSR2/2018/AMSR_U2_L3_SeaIce6km_*.he5")
    p = Pool()
    p.map_async(batch_reproj_roi, file_list)
    p.close()
    p.join()
    del p
