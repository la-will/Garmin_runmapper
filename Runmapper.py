import os
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import folium
import gpxpy
import webbrowser
from garminconnect import Garmin
import configparser

class GarminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Garmin GPX Downloader and Viewer")

        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self.load_config()

        # Section for downloading GPX files
        self.download_frame = tk.LabelFrame(root, text="Download GPX Files", padx=10, pady=10)
        self.download_frame.pack(padx=10, pady=10, fill="both", expand="yes")

        self.username_label = tk.Label(self.download_frame, text="Username:")
        self.username_label.grid(row=0, column=0, sticky="e")
        self.username_entry = tk.Entry(self.download_frame)
        self.username_entry.grid(row=0, column=1)

        self.password_label = tk.Label(self.download_frame, text="Password:")
        self.password_label.grid(row=1, column=0, sticky="e")
        self.password_entry = tk.Entry(self.download_frame, show='*')
        self.password_entry.grid(row=1, column=1)

        self.num_activities_label = tk.Label(self.download_frame, text="Number of Activities:")
        self.num_activities_label.grid(row=2, column=0, sticky="e")
        self.num_activities_entry = tk.Entry(self.download_frame)
        self.num_activities_entry.grid(row=2, column=1)
        self.num_activities_entry.insert(0, "10")  # Set default value to 10

        self.download_button = tk.Button(self.download_frame, text="Download GPX Files", command=self.download_gpx_files)
        self.download_button.grid(row=3, columnspan=2, pady=10)

        # Section for selecting and displaying HTML file
        self.display_frame = tk.LabelFrame(root, text="Display GPX Files", padx=10, pady=10)
        self.display_frame.pack(padx=10, pady=10, fill="both", expand="yes")

        self.select_directory_button = tk.Button(self.display_frame, text="Select GPX Directory", command=self.select_gpx_directory)
        self.select_directory_button.grid(row=0, columnspan=2, pady=10)

        self.directory_label = tk.Label(self.display_frame, text="No directory selected")
        self.directory_label.grid(row=1, columnspan=2)

        self.activity_label = tk.Label(self.display_frame, text="Select Activity Type:")
        self.activity_label.grid(row=2, column=0, sticky="e")
        self.activity_combobox = ttk.Combobox(self.display_frame, values=["running", "hiking", "cycling"])
        self.activity_combobox.grid(row=2, column=1)
        self.activity_combobox.current(0)  # Set default value

        self.display_button = tk.Button(self.display_frame, text="Display GPX Files", command=self.display_gpx_files)
        self.display_button.grid(row=3, columnspan=2, pady=10)

        self.gpx_directory = self.config.get('Settings', 'gpx_directory', fallback=None)
        if self.gpx_directory:
            self.directory_label.config(text=self.gpx_directory)

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def download_gpx_files(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        num_activities = int(self.num_activities_entry.get())

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        os.makedirs('gpx_files', exist_ok=True)

        try:
            client = Garmin(username, password)
            client.login()
            print("Login successful.")

            activities = client.get_activities(0, num_activities)  # Fetch the specified number of activities
            print(f"Fetched {len(activities)} activities.")

            map_center = [0, 0]  # Default center of the map
            map_zoom_start = 2   # Default zoom level
            gpx_map = folium.Map(location=map_center, zoom_start=map_zoom_start)

            for activity in activities:
                activity_id = activity['activityId']
                activity_type = activity['activityType']['typeKey']

                if activity_type in ['running', 'hiking']:
                    gpx_file_path = f'gpx_files/activity_{activity_id}.gpx'

                    gpx_data = client.download_activity(activity_id, dl_fmt=client.ActivityDownloadFormat.GPX)

                    with open(gpx_file_path, 'wb') as gpx_file:
                        gpx_file.write(gpx_data)
                    print(f"Downloaded GPX for {activity_type} activity {activity_id}.")

                    with open(gpx_file_path, 'r') as gpx_file:
                        gpx = gpxpy.parse(gpx_file)
                        for track in gpx.tracks:
                            for segment in track.segments:
                                points = [(point.latitude, point.longitude) for point in segment.points]
                                folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(gpx_map)

            html_file_path = 'gpx_map.html'
            gpx_map.save(html_file_path)
            print("All running and hiking activities have been processed and displayed on the map.")
            webbrowser.open(f'file://{os.path.realpath(html_file_path)}')

        except Exception as e:
            print(f"An error occurred: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def select_gpx_directory(self):
        self.gpx_directory = filedialog.askdirectory(title="Select Directory Containing GPX Files")
        if self.gpx_directory:
            self.directory_label.config(text=self.gpx_directory)
            self.config['Settings'] = {'gpx_directory': self.gpx_directory}
            self.save_config()
            print(f"Selected directory: {self.gpx_directory}")

    def display_gpx_files(self):
        if not self.gpx_directory:
            messagebox.showerror("Error", "Please select a directory containing GPX files.")
            return

        selected_activity = self.activity_combobox.get()
        map_center = [0, 0]  # Default center of the map
        map_zoom_start = 2   # Default zoom level
        gpx_map = folium.Map(location=map_center, zoom_start=map_zoom_start)

        total_distance = 0.0

        for gpx_file_name in os.listdir(self.gpx_directory):
            if gpx_file_name.endswith('.gpx'):
                gpx_file_path = os.path.join(self.gpx_directory, gpx_file_name)
                print(f"Processing GPX file: {gpx_file_path}")

                with open(gpx_file_path, 'r') as gpx_file:
                    gpx = gpxpy.parse(gpx_file)
                    for track in gpx.tracks:
                        if track.type == selected_activity:
                            for segment in track.segments:
                                points = [(point.latitude, point.longitude) for point in segment.points]
                                folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(gpx_map)
                                total_distance += segment.length_3d() / 1000  # Convert meters to kilometers

        # Add a legend to the map
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 90px; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; padding: 10px;">
        <b>Total Distance:</b><br>
        {total_distance:.2f} km
        </div>
        """
        gpx_map.get_root().html.add_child(folium.Element(legend_html))

        html_file_path = 'gpx_map.html'
        gpx_map.save(html_file_path)
        print(f"All {selected_activity} activities have been processed and displayed on the map.")
        webbrowser.open(f'file://{os.path.realpath(html_file_path)}')

if __name__ == "__main__":
    root = tk.Tk()
    app = GarminApp(root)
    root.mainloop()