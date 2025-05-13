#####################
# Block 1:  Import the packages you'll need
# 
# 

import os, sys
import rasterio
import geopandas as gpd
import numpy as np
from rasterstats import zonal_stats
import matplotlib.pyplot as plt
import pandas as pd


##################
# Block 2: 
# set the working directory to the directory where the data are

# Change this to the directory where your data are

data_dir = r"C:\Users\Public\Documents\Project_5"
os.chdir(data_dir)
print(os.getcwd())


##################
# Block 3: 
#   Set up a new smart raster class using rasterio  
#    that will have a method called "calculate_ndvi"
class SmartRasterio:
    def __init__(self, raster_path):
        self.raster_path = raster_path
    def calculate_ndvi(self, band4_index=4, band3_index=3):
        """Calculate NDVI using the NIR and Red bands."""
        okey = True
        try:
            with rasterio.open(self.raster_path) as src:
                # Read the bands as float32 arrays
                red = src.read(band3_index).astype('float32')
                nir = src.read(band4_index).astype('float32')
                self.meta = src.meta.copy()
        except Exception as e:
            okey = False
            print(f"Problem reading the file")
            print(e)
            return okey, None

        # Do the math to calculate NDVI
        try:
            ndvi = (nir - red) / (nir + red)
            ndvi = np.where((nir + red) == 0, 0, ndvi)
        except Exception as e:
            print(f"Problem in dividing the bands")
            print(e)
            return False, None

        # Update the metadata based on the original raster
        self.meta.update({
            "count": 1,
            "dtype": 'float32',
            "driver": 'GTiff',
        })

        return okey, ndvi

##################
# Block 4: 
#   Set up a new smart vector class using geopandas
#    that will have a method similar to what did in lab 4
#    to calculate the zonal statistics for a raster
#    and add them as a column to the attribute table of the vector
class SmartVectorLayer:
    def __init__(self, feature_class_path):
        """Initialize with a path to a vector file (e.g., shapefile, GeoPackage, etc.)"""
        self.feature_class = feature_class_path
        try:
            self.gdf = gpd.read_file(self.feature_class)
        except Exception as e:
            print(f"Could not read {self.feature_class}: {e}")

    def summarize_field(self, field):
        """Calculate the mean of a numeric field using geopandas."""
        okay = True

        # Check if the field exists
        if field not in self.gdf.columns:
            print(f"The field {field} is not in the list of possible fields.")
            return False, None

        # Calculate the mean, ignoring NaN values
        try:
            vals = self.gdf[field].dropna()
            mean = np.mean(vals)
            return okay, mean
        except Exception as e:
            print(f"Problem calculating mean: {e}")
            okay = False
            return okay, None

  

    def zonal_stats_to_field(self, raster_path, statistic_type="mean", output_field="ZonalStat"):
        """
        For each feature in the vector layer, calculates the zonal statistic from the raster
        and writes it to a new field.

        Parameters:
        - raster_path: path to the raster
        - statistic_type: type of statistic ("mean", "sum", etc.)
        - output_field: name of the field to create to store results
        """
        okay = True

        # Check if the field already exists
        if output_field in self.gdf.columns:
            print(f"The field {output_field} already exists. It will be overwritten.")
            self.gdf = self.gdf.drop(columns=[output_field])

        # Calculate zonal statistics
        try:
            stats = zonal_stats(
                self.gdf, raster_path, stats=statistic_type.lower(), geojson_out=False, nodata=-9999
            )
            # Extract the statistic values and add as a new column
            stat_values = [s[statistic_type.lower()] if s[statistic_type.lower()] is not None else np.nan for s in stats]
            self.gdf[output_field] = stat_values
        except Exception as e:
            print(f"Problem calculating zonal stats: {e}")
            okay = False
            return okay

        print(f"Zonal statistics '{statistic_type}' written to field '{output_field}'.")
        return okay
    

    def extract_to_pandas_df(self, fields=None):
        """
        Extracts attribute data from the vector layer to a pandas DataFrame.
        If fields is None, all non-geometry columns are extracted.
        """
        okay = True

        # If no fields specified, use all non-geometry columns
        if fields is None:
            fields = [col for col in self.gdf.columns if col.lower() != 'geometry']
        else:
            # Check that all requested fields exist and are not geometry
            true_fields = [col for col in self.gdf.columns if col.lower() != 'geometry']
            disallowed = [user_f for user_f in fields if user_f not in true_fields]
            if len(disallowed) != 0:
                print("Fields given by user are not valid for this table")
                print(disallowed)
                okay = False
                return okay, None

        # Extract the data
        try:
            df = self.gdf[fields].copy()
        except Exception as e:
            print(f"Problem extracting fields: {e}")
            okay = False
            return okay, None

        return okay, df
    

class SmartGeoPanda(gpd.GeoDataFrame):
    @property
    def _constructor(self):
        return SmartGeoPanda

    def scatterplot(self, x_field, y_field, title=None, 
                    x_min=None, x_max=None, 
                    y_min=None, y_max=None):
        """Make a scatterplot of two columns, with validation."""
        for field in [x_field, y_field]:
            if field not in self.columns:
                raise ValueError(f"Field '{field}' not found in DataFrame columns.")

        df_to_plot = self
        if x_min is not None:
            df_to_plot = df_to_plot[df_to_plot[x_field] >= x_min]
        if x_max is not None:
            df_to_plot = df_to_plot[df_to_plot[x_field] <= x_max]
        if y_min is not None:
            df_to_plot = df_to_plot[df_to_plot[y_field] >= y_min]
        if y_max is not None:
            df_to_plot = df_to_plot[df_to_plot[y_field] <= y_max]

        plt.figure(figsize=(8,6))
        plt.scatter(df_to_plot[x_field], df_to_plot[y_field])
        plt.xlabel(x_field)
        plt.ylabel(y_field)
        plt.title(title if title else f"{y_field} vs {x_field}")
        plt.grid(True)
        plt.show()

    def mean_field(self, field):
        """Get mean of a field, ignoring NaN."""
        return self[field].mean(skipna=True)

    def save_scatterplot(self, x_field, y_field, outfile, title=None, 
                         x_min=None, x_max=None, 
                         y_min=None, y_max=None):
        """Make a scatterplot of two columns, with validation and save to file."""
        for field in [x_field, y_field]:
            if field not in self.columns:
                raise ValueError(f"Field '{field}' not found in DataFrame columns.")

        df_to_plot = self
        if x_min is not None:
            df_to_plot = df_to_plot[df_to_plot[x_field] >= x_min]
        if x_max is not None:
            df_to_plot = df_to_plot[df_to_plot[x_field] <= x_max]
        if y_min is not None:
            df_to_plot = df_to_plot[df_to_plot[y_field] >= y_min]
        if y_max is not None:
            df_to_plot = df_to_plot[df_to_plot[y_field] <= y_max]

        plt.figure(figsize=(8,6))
        plt.scatter(df_to_plot[x_field], df_to_plot[y_field])
        plt.xlabel(x_field)
        plt.ylabel(y_field)
        plt.title(title if title else f"{y_field} vs {x_field}")
        plt.grid(True)
        plt.savefig(outfile)
        plt.close()


    def plot_from_file(self, csv_control_file_path):
        """
        Reads a CSV control file with plotting parameters and creates a scatterplot.
        """
        try:
            params = pd.read_csv(csv_control_file_path)
        except Exception as e:
            print(f"Problem reading the {csv_control_file_path}")
            return False

        try:
            param_dict = {str(k).strip(): v for k, v in zip(params['Param'], params['Value'])}
        except Exception as e:
            print(f"Problem setting up dictionary: {e}")
            return False

        # Required parameters
        required_params = ["x_field", "y_field", "outfile"]
        missing = [m for m in required_params if m not in param_dict.keys()]
        if missing:
            print("The param file needs to have these additional parameters")
            print(missing)
            return False

        # Optional parameters
        optional_params = ["x_min", "x_max", "y_min", "y_max"]
        for p in optional_params:
            if p not in param_dict:
                param_dict[p] = None
            else:
                # Convert to float if not None or empty
                if param_dict[p] not in [None, '', 'None']:
                    try:
                        param_dict[p] = float(param_dict[p])
                    except Exception:
                        param_dict[p] = None

        # Do the plot
        try:
            self.save_scatterplot(
                param_dict['x_field'],
                param_dict['y_field'],
                param_dict['outfile'],
                x_min=param_dict['x_min'],
                x_max=param_dict['x_max'],
                y_min=param_dict['y_min'],
                y_max=param_dict['y_max']
            )
            print(f"wrote to {param_dict['outfile']}")
            return True
        except Exception as e:
            print(f"Problem saving the scatterplot: {e}")
            return False    






