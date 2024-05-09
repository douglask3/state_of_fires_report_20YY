graphics.off()
library(stringr) 
source("../LPX_equil/libs/legendColBar.r")
source("libs/find_levels.r")

dir = "outputs/ConFire_Canada-nrt-tuning9/figs/_12-frac_points_0.5-baseline-control_TS/pc-95/"
files = c("points-Control.csv",
	  "points-standard-Fuel.csv",
	  "points-standard-Moisture.csv",
	  "points-standard-Weather.csv",
	  "points-standard-Ignition.csv",
	  "points-standard-Suppression.csv")


levels = c(0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
cols = list(c('#ffffcc','#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c','#bd0026','#800026', '#400013'),
			c('#ffffe5','#f7fcb9','#d9f0a3','#addd8e','#78c679','#41ab5d','#238443','#006837','#004529', '#002315'),
		    rev(c('#ffffd9','#edf8b1','#c7e9b4','#7fcdbb','#41b6c4','#1d91c0','#225ea8','#253494','#081d58', '#041034')),
			c('#f7f4f9','#e7e1ef','#d4b9da','#c994c7','#df65b0','#e7298a','#ce1256','#980043','#67001f', '#340014'),
			c('#fff5f0','#fee0d2','#fcbba1','#fc9272','#fb6a4a','#ef3b2c','#cb181d','#a50f15','#67000d', '#340202'),
			c('#fff5f0','#f0f0f0','#d9d9d9','#bdbdbd','#969696','#737373','#525252','#252525','#131313', '#340202'))

dlevels = c(-0.05, -0.02, -0.01, -0.005, -0.002, -0.001, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05)
dcols = list(rev(c('#35000f', '#67001f','#b2182b','#d6604d','#f4a582','#fddbc7','#f0f0f0','#d1e5f0','#92c5de','#4393c3','#2166ac','#053061', '#031531')),
			 c('#400131', '#8e0152','#c51b7d','#de77ae','#f1b6da','#fde0ef','#f7f7f7','#e6f5d0','#b8e186','#7fbc41','#4d9221','#276419', '#153210'),
			 rev(c('#301503', '#543005','#8c510a','#bf812d','#dfc27d','#f6e8c3','#f5f5f5','#c7eae5','#80cdc1','#35978f','#01665e','#003c30', '#001c15')),
			 rev(c('#501a04', '#7f3b08','#b35806','#e08214','#fdb863','#fee0b6','#f7f7f7','#d8daeb','#b2abd2','#8073ac','#542788','#2d004b', '#19002b')),
			 rev(c('#730013', '#a50026','#d73027','#f46d43','#fdae61','#fee090','#ffffbf','#e0f3f8','#abd9e9','#74add1','#4575b4','#313695', '#100019')),
			 rev(c('#20002a', '#40004b','#762a83','#9970ab','#c2a5cf','#e7d4e8','#f7f7f7','#d9f0d3','#a6dba0','#5aae61','#1b7837','#00441b', '#002210')))
			 
cut_results <- function(x, breaks) {
	out = x
	out[] = 0
	for (i in 1:length(breaks)) 
		out[x > breaks[i]] = i
	return(out)
}

split_to_day <- function(x) 
	#approx(1:length(x), x, seq(1, length(x), by = 1/30))[[2]]
	predict(smooth.spline(1:length(x), x), 
		    seq(0.5, length(x)+0.5, by = 1/30))[[2]]

find_clim_av <- function(x) 
	 sapply(1:360, function(day) mean(x[seq(day, length(x), by = 360)]))



plot_strpes <- function(cdat, levels, cols) {
	cdat = cut_results(cdat, levels)

	plot(c(1, 365), ncol(cdat) * c(-1, 1), type = 'n', axes = FALSE, xlab = '', ylab = '')
        
	add_Day <- function(day) {
		add_enemble <- function(ens) {
			x = day + 0.5 * c(-1, 1)
			y = c(ens, ens)
			lines(x, y, col = cols[z[ens]], lwd = 2)
			lines(x, -y, col = cols[z[ens]], lwd = 2)
		}
		z = rev(sort(cdat[day,]))
		lapply(1:ncol(cdat), add_enemble)
	}

	sapply(1:360, add_Day)
	axis(at = seq(15, 360-15, 30), labels = month.abb, side = 1, pos = 0)
	axis(at = c(-260, 700), labels = c('', ''), side = 1, pos = 0, xpd = FALSE)
}


plot_cols <- function(file, cols, levels = NULL, do_last_year = FALSE, do_anom = FALSE) {   
	dat = as.matrix(read.csv(paste0(dir, file), stringsAsFactors = FALSE))*100
	idat = apply(dat, 1, split_to_day)
        
	clim = apply(idat, 2, find_clim_av)
        
	if (do_anom) {
	    if (file == files[1]) 
                clim = tail(idat, 360) - clim
            else
                clim = log(tail(idat, 360)) - log(clim)
	    #levels = quantile(abs(clim), seq(0, 1, length.out = ceiling(length(cols))/2))[-1]
	    #levels = c(rev(-levels), levels)
            extend_min = TRUE
            minLab = ''
	} else {
            if (do_last_year) clim = tail(idat, 360)
	    #levels =  head(quantile(dat, seq(0, 1, length.out = length(cols) + 1))[-1], -1)
            extend_min = FALSE
            minLab = 0
	}
        if (is.null(levels)) levels = find_levels_n(clim, 9, TRUE)
        levels = unique(signif(levels), 2)
        cols =  make_col_vector(cols, ncols = length(levels) + 1)
	
	plot_strpes(clim, levels, cols)
        if (file == files[1]) {
            if (do_anom) mtext(side = 3, line = 1, 'anomoly')
                else if (do_last_year) mtext(side = 3, line = 1, '2023')
                else mtext(side = 3, line = 1, 'Climatology')
        }
        if (!do_anom && !do_last_year) {
            if (grepl('Control', file)) {
                txt = 'Burnt\nArea'
            } else {
                txt = gsub('-', ' ', gsub('.csv', '', gsub("points-", "", file)))
                txt = str_to_title(txt)
                txt = gsub(' ', '\n', txt)
            }
            mtext(side = 2, line = 1, txt)
        }
        legendColBar(c(365, 380), ncol(clim) * c(-0.9, 0.9), cols, levels, extend_max=TRUE, 
                     extend_min = extend_min, minLab = minLab, add = TRUE, xtext_pos_scale= 1.4)
        return(levels)
        
}

png("figs/control_stripes.png", height = 6.5, width = 10, units = 'in', res = 300)
par(mfcol = c(6, 3), mar = c(0, 2, 0, 0), oma = c(0,2, 2, 3.5))

levels = mapply(plot_cols, files, cols, SIMPLIFY = FALSE)

mapply(plot_cols, files, cols, levels = levels, MoreArgs = list(do_last_year = TRUE))
mapply(plot_cols, files, dcols, MoreArgs = list(do_anom = TRUE))
dev.off()
