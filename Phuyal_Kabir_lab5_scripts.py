# Lab 5 scripts
import numpy as np
import Phuyal_kabir_lab5_functions as l5
import matplotlib.pyplot as plt
#  Part 1:

#  Assign a variable to the Landsat file 

landsat_file = r"C:\Users\Public\Documents\Project_5\Data\Landsat_image_corv.tif"
smart_raster = l5.SmartRasterio(landsat_file)
ok, ndvi = smart_raster.calculate_ndvi()


# Calculate NDVI and save to and output file
if ok:
    ndvi_output = r"C:\Users\Public\Documents\Project_5\Data\ndvi_output.tif"
    with l5.rasterio.open(
        ndvi_output, 'w', **smart_raster.meta
    ) as dst:
        dst.write(ndvi.astype('float32'), 1)
    print(f"NDVI saved to {ndvi_output}")


    # Part 2:
# Assign a variable to the parcels data shapefile path
    parcels_file = r"C:\Users\Public\Documents\Project_5\Data\Benton_County_TaxLots.shp"

        # Zonal statistics
    #  Pass this to your new smart vector class
    smart_vector = l5.SmartVectorLayer(parcels_file)
    ok2 = smart_vector.zonal_stats_to_field(
        raster_path=ndvi_output,
        statistic_type="mean",
        output_field="mean_ndvi"
    )
 #  Calculate zonal statistics and add to the attribute table of the parcels shapefile   
    if ok2:
        print("Zonal statistics calculated and added to the attribute table.")
        smart_vector.gdf.to_file(
            r"C:\Users\Public\Documents\Project_5\Data\Benton_County_TaxLots_with_ndvi.gpkg",
            driver="GPKG"
        )
        # Choropleth map
        ax = smart_vector.gdf.plot(
            column="mean_ndvi",
            cmap="Reds",           # Use a red gradient
            legend=True,
            figsize=(10, 8),
            edgecolor='k',         # Optional: black borders for clarity
            linewidth=0.2
        )
#  Part 3: Optional
#  Use matplotlib to make a map of your census tracts with the average NDVI values
        ax.set_title("Average NDVI by Parcel (Red Gradient)")
        plt.axis('off')
        plt.tight_layout()
        plt.show()

        # Scatter plot (replace SOME_OTHER_FIELD with your actual field name)
        from lab5_functions import SmartGeoPanda
        # Scatter plot: YEAR_BUILT vs. NDVI_mean
        if "YEAR_BUILT" in smart_vector.gdf.columns and "mean_ndvi" in smart_vector.gdf.columns:
            plt.figure(figsize=(8,6))
            plt.scatter(smart_vector.gdf["YEAR_BUILT"], smart_vector.gdf["mean_ndvi"], alpha=0.6, color='red', edgecolor='k')
            plt.xlabel("Year Built")
            plt.ylabel("Mean NDVI")
            plt.title("Scatter Plot of Mean NDVI vs. Year Built")
            plt.xlim(1901,2030)
            plt.ylim(-1,1)
            plt.grid(True)
            plt.tight_layout()
            plt.show()
        else:
            print("YEAR_BUILT or mean_ndvi not found in data. Scatter plot not created.")
    else:
        print("Zonal statistics calculation failed.")
else:
    print("NDVI calculation failed.")

# Part 3: (Optional) Plotting
# You can use the plot_field method if you implemented it:
# smart_vector.plot_field("mean_ndvi", title="Mean NDVI by Parcel")

# Part 2:
# Assign a variable to the parcels data shapefile path


#  Pass this to your new smart vector class


#  Calculate zonal statistics and add to the attribute table of the parcels shapefile




#  Part 3: Optional
#  Use matplotlib to make a map of your census tracts with the average NDVI values








