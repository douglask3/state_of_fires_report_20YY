import sys
sys.path.append('../libs/')
sys.path.append('libs/')

from read_variable_from_netcdf import *
from combine_path_and_make_dir import *
from plot_maps import *
import os
from pathlib import Path

from   io     import StringIO
import numpy  as np
import math
import glob
import hashlib

import matplotlib.pyplot as plt
from pdb import set_trace

def read_variable_from_netcdf_stack(filenames, example_cube = None, 
                                    *args, **kw):
    
    cubes = [read_variable_from_netcdf(file, *args, **kw) for file in filenames]
    cubes = [cube for cube in cubes if cube is not None]
    cubes = iris.cube.CubeList(cubes)
    try:
        cubes = cubes.concatenate_cube()
    except:
        iris.util.equalise_attributes(cubes)
        cubes = cubes.concatenate_cube()
    
    if example_cube is not None:
        example_cube = iris.load_cube(example_cube)
        
        cubes = cubes.regrid(example_cube, iris.analysis.Linear())
        cubes.data = np.ma.masked_greater(cubes.data, 9E9)
        cubes.data[cubes.data > 9E9] = np.nan
    return cubes

def generate_temp_fname(string1, string2):
    string = string1 + string2
    return '../temp/isimip_dat_gen-' + hashlib.sha256(string.encode()).hexdigest() + '.txt'

def make_variables_for_year_range(year, process, dir):
    def test_if_process(var, temp_file = None): 
        if temp_file is not None and os.path.isfile(temp_file) and grab_old_data:
            out = False
        else:
            out = any(i == var for i in process)
        return out
    output_year = str(year[0]) + '_' + str(year[1])

    temp_out = dir + output_year
    print(temp_out)
    def open_variable(varname, plusMinusYr = False):
        filename = filenames[varname]
        file_years = set([file[-12:-3] for file in glob.glob(dir + '*')]) 
        file_years = list(file_years)
        try:
            yeari = year.copy()
        except:
            set_trace()
        if plusMinusYr:
            yeari[0] = yeari[0] - 1
            yeari[1] = yeari[1] + 1
        
        file_years_ranges = [(int(pair.split('_')[0]), int(pair.split('_')[1])) \
                             for pair in file_years]
        # Find overlapping elements
        overlapping_years = []
        for i, range_pair in enumerate(file_years_ranges):
            if yeari[1] >= range_pair[0] and yeari[0] <= range_pair[1]:
                overlapping_years.append(file_years[i])
        #set_trace()
        filename = [filename + ext + '.nc' for ext in overlapping_years]
        
        sbs_funs = [sub_year_range] + subset_functions 
        sbs_args = [{'year_range': yeari}] + subset_function_argss
         
        out = None
        out =  read_variable_from_netcdf_stack(filename, example_cube, dir,
                                               subset_function = sbs_funs, 
                                               subset_function_args = sbs_args)
        return out

    def monthly_mean(cube, fun = iris.analysis.MEAN):
        return cube.aggregated_by(['year', 'month'], fun)

    def save_ncdf(cube, varname): 
        
        out_dir = output_dir + '/' + \
                    subset_function_argss[0][next(iter(subset_function_argss[0]))] + '/' + \
                    dataset_name + '/period_' + output_year + '/'
        
        if not os.path.exists(out_dir): Path(out_dir).mkdir(parents=True)
        
        iris.save(cube, out_dir + '/' + varname +  '.nc')

    def standard_Monthly_mean(var, fun):
        temp_file = generate_temp_fname(temp_out, var)
        if test_if_process(var, temp_file):
            dat = open_variable(var)
            mdat = monthly_mean(dat, fun)
            save_ncdf(mdat, var + '_mean') 
            open(temp_file, 'a').close()   

    def cal_cover(cover_vars, name):
        print(name)
        dat = open_variable(cover_vars[0])
        
        for i in cover_vars[1:]:
            dat.data = dat.data + open_variable(i).data
        dat.rename(name)
        save_ncdf(dat, name + '_jules-es')
        return dat

    for var, fun in zip(process_standard, process_function):
        standard_Monthly_mean(var, fun) 
   
    
    temp_file = generate_temp_fname(temp_out, 'cover')
    if test_if_process('cover', temp_file):
        tree_vars = ["bdldcd", "bdlevgtemp", "bdlevgtrop", "ndldcd", "ndlevg", \
                     "shrubdcd", "shrubevg"]
        herb_vars = ["c3crop", "c3grass", "c3pasture", "c4crop", "c4grass", "c4pasture"]
        soil_vars = ["soil", "urban", "ice"] # water
        
        cal_cover(tree_vars, 'tree_cover')
        cal_cover(herb_vars, 'nonetree_cover')
        cal_cover(herb_vars, 'noneveg_cover')
        open(temp_file, 'a').close()
    
    temp_file = generate_temp_fname(temp_out, 'crop')
    if test_if_process('crop', temp_file)  : 
        cal_cover(["c3crop", "c4crop"], 'crop')
        open(temp_file, 'a').close()
    

    temp_file = generate_temp_fname(temp_out, 'pature')
    if test_if_process('pature', temp_file): 
        cal_cover(["c3pasture", "c4pasture"], 'pasture')
        open(temp_file, 'a').close()

    temp_file = generate_temp_fname(temp_out, 'urban')
    if test_if_process('urban', temp_file): 
        cal_cover(["urban"], 'urban')
        open(temp_file, 'a').close()
        
    temp_file_tas = generate_temp_fname(temp_out, 'tas')
    temp_file_vpd = generate_temp_fname(temp_out, 'vpd')
    if test_if_process('tas', temp_file_tas) or test_if_process('vpd', temp_file_vpd):
        tas = open_variable('tas')
        tas_range = open_variable('tas_range')
        
        tas_max = tas.copy()
        tas_max.data  = tas_max.data + 0.5 * tas_range.data

        if test_if_process('vpd', temp_file_vpd):
            def SVP(temp):
                svp = temp.copy()
                
                svp = svp - 273.16
                svp.data =  610.78 * np.exp(svp.data / (svp.data +237.3) * 17.2694)
                return svp

            sh = open_variable("huss")
            ps = open_variable("ps")

            rh = sh.copy()
            rh.data = 0.263 * sh.data * ps.data / \
                        np.exp(17.67 * (tas_max.data -273.16)/(tas_max.data - 29.65))

            svp = SVP(tas_max)
            vpd = svp*(1.0-rh*0.01)
            
            vpd.data[vpd.data<0.0] = 0.0            
            vpd_mean_monthly = monthly_mean(vpd)   
            vpd_max_monthly = monthly_mean(vpd, iris.analysis.MAX)
            
            save_ncdf(vpd_max_monthly, 'vpd_max')
            save_ncdf(vpd_mean_monthly, 'vpd_mean')
            
            open(temp_file_vpd, 'a').close()
            
        if test_if_process('tas'):
            
            tas_monthly = monthly_mean(tas)
            tas_max_monthly = tas.aggregated_by(['year', 'month'], iris.analysis.MAX)

            save_ncdf(tas_monthly, 'tas_mean')
            save_ncdf(tas_max_monthly, 'tas_max')
            open(temp_file_tas, 'a').close()
     
    temp_file = generate_temp_fname(temp_out, 'pr')       
    if test_if_process('pr'):
        pr = open_variable('pr', True)
        pr_mean = monthly_mean(sub_year_range(pr, year))
        
        dry_days = pr.copy()
        dry_days.data[dry_days.data < (1.0/86400.0)] = 0.0
        dry_days.data[dry_days.data > 0.0] = 1.0
        dry_days.data = 1.0 - dry_days.data
        dry_days.units = '1'

        def cummDry(data):
            if np.isnan(data[0]): return data
            try: 
                if data.mask[0]: return data
            except:
                pass
                
            out = data.copy()
            out[:] = 0.0
            for i in range(1, len(out)):
                if data[i] > 0.0: out[i] = out[i-1] + 1
            return out

        consec_dry = dry_days.copy()
        consec_dry.data = np.apply_along_axis(cummDry, 0, dry_days.data)
        
        dry_days_mean = monthly_mean(sub_year_range(dry_days, year))
        consec_dry_mean = monthly_mean(sub_year_range(consec_dry, year), iris.analysis.MAX)
            
        save_ncdf(pr_mean, 'pr_mean')
        save_ncdf(dry_days_mean, 'dry_days')
        save_ncdf(consec_dry_mean, 'consec_dry_mean')
        open(temp_file, 'a').close()

filenames = {"tas": "tas_global_daily_",
             "tas_range": "tas_range_global_daily_",
             "pr": "pr_global_daily_",
             "prsn": "ps_global_daily_",
             "hurs": "hurs_global_daily_",
             "huss": "huss_global_daily_",
             "sfcwind": "sfcwind_global_daily_",
             "ps": "ps_global_daily_",
             "bdldcd": "bdldcd_global_annual_",
             "bdlevgtemp": "bdlevgtemp_global_annual_",
             "bdlevgtrop": "bdlevgtrop_global_annual_",
             "c3crop": "c3crop_global_annual_",
             "c3grass": "c3grass_global_annual_",
             "c3pasture": "c4pasture_global_annual_",
             "c4crop": "c4crop_global_annual_",
             "c4grass": "c4grass_global_annual_",
             "c4pasture": "c4pasture_global_annual_",
             "ice": "ice_global_annual_",
             "lake": "lake_global_annual_",
             "urban": "urban_global_annual_",
             "ndldcd": "ndldcd_global_annual_",
             "ndlevg": "ndlevg_global_annual_",
             "shrubdcd": "shrubdcd_global_annual_",
             "shrubevg": "shrubevg_global_annual_",
             "soil": "soil_global_annual_",
             "total":  "total_global_annual_"}


process_standard = ['prsn', "hurs", "hurs", "huss", "huss", "sfcwind"]
process_function = [iris.analysis.MEAN, 
                    iris.analysis.MEAN, iris.analysis.MAX,
                    iris.analysis.MEAN, iris.analysis.MAX,
                    iris.analysis.MAX]

process_clim = ['vpd', 'tas', 'tas_range', 'pr']
process_jules =['cover', 'crop', 'pasture', "urban"]

example_cube = None
grab_old_data = False

subset_functions = [ar6_region]
subset_function_argss = [{'region_code': 'NWN'}]
output_dir = "../data/data/driving_data/"

def process_clim_and_jules():
    def process(process, dir):
        [make_variables_for_year_range(year, process, dir) for year in  years]
    process(process_jules, dir_jules)
    process(process_clim, dir_clim)
    
if __name__=="__main__":
    dir_clim = "/hpc//data/d00/hadea/isimip3a/InputData/climate/atmosphere/obsclim/GSWP3-W5E5/gswp3-w5e5_obsclimfill_"
    dir_jules = "/scratch/hadea/isimip3a/u-cc669_isimip3a_es/GSWP3-W5E5_obsclim/jules-es-vn6p3_gswp3-w5e5_obsclim_histsoc_default_pft-"
    
    file_years_clim = ["1901_1910", "1911_1920", "1991_2000", "2001_2010", "2011_2019"]
    file_years_jules = ["1901_2019"]
    years = [[2010, 2012], [1901, 1920], [2000, 2019], [2002, 2019]]
    dataset_name = 'isimp3a/GSWP3-W5E5'
    
    #output_years = ['2010_2012', '1901_1920', '2000_2019', '2002_2019']
    
    process_clim_and_jules()    


    filenames = {"tas": "tasAdjust_global_daily_",
             "tas_range": "tas_rangeAdjust_global_daily_",
             "pr": "prAdjust_global_daily_",
             "prsn": "psAdjust_global_daily_",
             "hurs": "hursAdjust_global_daily_",
             "huss": "hussAdjust_global_daily_",
             "sfcwind": "sfcwindAdjust_global_daily_",
             "ps": "psAdjust_global_daily_",
             "bdldcd": "bdldcd_global_annual_",
             "bdlevgtemp": "bdlevgtemp_global_annual_",
             "bdlevgtrop": "bdlevgtrop_global_annual_",
             "c3crop": "c3crop_global_annual_",
             "c3grass": "c3grass_global_annual_",
             "c3pasture": "c4pasture_global_annual_",
             "c4crop": "c4crop_global_annual_",
             "c4grass": "c4grass_global_annual_",
             "c4pasture": "c4pasture_global_annual_",
             "ice": "ice_global_annual_",
             "lake": "lake_global_annual_",
             "urban": "urban_global_annual_",
             "ndldcd": "ndldcd_global_annual_",
             "ndlevg": "ndlevg_global_annual_",
             "shrubdcd": "shrubdcd_global_annual_",
             "shrubevg": "shrubevg_global_annual_",
             "soil": "soil_global_annual_",
             "total":  "total_global_annual_"}


    #file_years_clims = ["1961_1970", "1971_1980", "1981_1990", "1991_2000", "2001_2010", "2011_2014"]
    #file_years_jules = ["1850_2014"]
    futr_years = [[2015, 2099]]
    yearss = [[[1994, 2014]],futr_years, futr_years, futr_years]
    ismip3b_models = ['GFDL-ESM4', 'IPSL-CM6A-LR', 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'UKESM1-0-LL']
    codes = ['r1i1p1f1', 'r1i1p1f1', 'r1i1p1f1', 'r1i1p1f1', 'r1i1p1f2']
    experiments = ['historical', 'ssp126', 'ssp370', 'ssp585']
    socs = ['histsoc', '2015soc', '2015soc', '2015soc']
    
    for experiment, soc, years in zip(experiments, socs, yearss):
        for model, code in zip(ismip3b_models, codes):
            dir_clim = '/hpc//data/d00/hadea/isimip3b/InputData/climate/atmosphere/' + \
                            experiment + '/'+  model + '/' + model.lower() + '_' + \
                            code + '_w5e5_' + \
                            experiment + '_'  
            dir_jules =  '/scratch/hadea/isimip3b/u-cc669_isimip3b_es/' + model + '_' + \
                            experiment + '/' + \
                    'jules-es-vn6p3_' + model.lower() + \
                    '_w5e5_' + experiment +'_' + soc + '_default_pft-' 
            dataset_name = 'isimp3b/' +  experiment + '/' + model + '/'
    
            process_clim_and_jules()    

    
        #for i in range(len(ismip3b_models)):
        #    dir_clim = dirs_clim[i]
        #    dir_jules = dirs_jules[i]
        #    dataset_name = dataset_names[i]
        #    process_clim_and_jules()    
    
    obs_cover_dir = '/home/h02/dkelley/state_of_fires_report_20YY/data/data/driving_data/Canada_extended/'

    output_years = '2002_2019'
    years = [2002, 2019]
    files = os.listdir(obs_cover_dir)

    def open_regrid_output_file(filename):
        if '-raw' in filename: return None
        cube = iris.load_cube(obs_cover_dir + filename)
        cube0 = cube.copy()
        cube = sub_year_range(cube, years)
        for fun, args in zip(subset_functions, subset_function_argss):
            cube = fun(cube, **args)
        out_fname = output_dir + '/' + \
                    subset_function_argss[0][next(iter(subset_function_argss[0]))] + '/' + \
                    dataset_name + '/period_' + output_years + '/' + \
                    filename[:-3] + '_VCF-obs.nc'
        iris.save(cube, out_fname)

    for filename in files: open_regrid_output_file(filename)

    #sbs_funs = [sub_year_range] + subset_functions 
    #sbs_args = [{'year_range': yeari}] + subset_function_argss
