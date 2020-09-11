# coding=utf-8
from __future__ import absolute_import
import requests
import re
from file_read_backwards import FileReadBackwards
import json

### RPL Logger
# This plugin simply logs printer data to a website. By default, the website is a Rails server hosted on Taz6.
# This website has a RESTful API which allows for the creation and management of "Printers" and "Print logs" 
# (Quotation marks used to represent the models in the  Rails server)
# When Octoprint starts up, it POSTs a "printer" to the website to ensure that it exists, & if it already does, the server ignores 
# the request. When a print is started, two POST requests are sent. One to update the status of the "printer", and the other to 
# create a new "Print Log". If the print fails or is cancelled, two POST requests are sent. One to update the status of the "printer",
# and another to update the status of the "print log". If the print succeeds, two post requests are sent. One to update the status of the printer
# and another to update the status of the "print log".
# 
# Status Chart:
# 0 = idle
# 1 = printing
# 2 = success
# 3 = failed

import octoprint.plugin

class RplloggerPlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.EventHandlerPlugin):
    
    # This value the id of the print log, generated by the Rails server.
    print_log_id = None

    ##~~ SettingsPlugin mixin

    # These are the default values for the plugin's settings. These values
    # can be changed through the Octoprint Web Interface
    def get_settings_defaults(self):
        return dict(
            url="http://10.147.20.155:3000",
            printer_name="",
            authentication_token=""
        )

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ EventPlugin Mixin

    def on_event(self, event, payload):
        # If there is no printer name, ignore this plugin
        if self.get_printer_name() == "":
            return

        if event == "PrintStarted":
            self.on_print_started(payload)
        elif event == "PrintFailed" or event == "PrintCancelled":
            self.on_print_stopped(payload)
        elif event == "PrintDone":
            self.on_print_done(payload)
        elif event == "Startup":
            self.create_printer()

    def on_print_started(self, payload):
        # UPDATE status of printer to "printing" state
        self.update_printer_status(1)
        # CREATE PRINT LOG
        self.create_print_log(payload)

    def on_print_stopped(self, payload):
        # UPDATE status of printer to "idle" state
        self.update_printer_status(0)
        # UPDATE log status to "failed" state
        self.update_print_log(3)

    def on_print_done(self, payload):
        # UPDATE status of printer to "successful" state
        self.update_printer_status(2)
        # UPDATE log status to "successful" state
        self.update_print_log(2)


    ##~~ Helper Methods

    def get_url(self):
        return self._settings.get(["url"])

    def get_api_path(self):
        return self._settings.get(["url"]) + "/api/v1/"

    def get_printer_name(self):
        return self._settings.get(["printer_name"])

    def get_file_path(self):
        return "/home/pi/.octoprint/uploads/"

    def set_log_id(self, string_payload):
        self.print_log_id = json.loads(string_payload)["id"]

    # Create Printer if_not_exists
    def create_printer(self):
        url = self.get_api_path() + "printers_api"
        name = self.get_printer_name()
        payload = {"name" : self.get_printer_name(), "status" : "0"}

        result = requests.post(url, data = payload)
        self.log("Printer Created: " + name)

    def update_printer_status(self, status):
        name = self.get_printer_name()
        url = self.get_api_path() + "printers_api/edit"
        payload = {"name" : name, "status" : str(status)}

        result = requests.post(url, data = payload)
        self.log("Printer Status updated to: " + str(status))

    def create_print_log(self, payload):
        url = self.get_api_path() + "print_logs_api"
        name = self.get_printer_name()
        metadata = self.find_meta_data(payload["path"], 'Build time', 'Plastic weight')
        payload = { "printer_name" : name, 
                    "file_name" : payload["name"], 
                    "status" : "1", 
                    "print_time" : metadata["Build time"],
                    "filament_weight" : metadata["Plastic weight"]}

        result = requests.post(url, data = payload)
        self.set_log_id(result.text)
        self.log("Printer Status updated to: 1")

    def update_print_log(self, status):
        if self.print_log_id == None: return

        url = self.get_api_path() + "print_logs_api/edit"
        payload = {"id" : self.print_log_id, "status" : status}
        result = requests.post(url, data = payload)
        self.log("Printer Status updated to: " + status)

    def log(self, message):
        self._logger.info("********** RPL LOGS => " + message)
        

    ##~~ Extract Meta Data
    # These two functions parse a .gcode file for it's metadata. Since the RPL uses Simplify3D for slicing,
    # each .gcode file has comments with the ETA, Filament Weight and a couple other things. Since the goal
    # of the plugin is to log print data, those two things are important. Some of the data is at the beginning 
    # of the file, and some is at the end. As a result, the file is opened both normally and reversed to skip all
    # the gcode commands. We just need the comments.
    def find_meta_data(self, path, *args):
        # initial setup
        path = self.get_file_path() + path
        dictionary = dict()
        for arg in args:
            dictionary[arg] = ""

        # read_file_line_by_line()
        with open(path) as file:
            for line in file:
                if line.startswith(";"):
                    self.examine_line(dictionary, line, ",")
                else:
                    file.close()
                    break

        # self.__reverse_read_file()
        file = FileReadBackwards(path)
        for line in file:
            if line.startswith(";") and ":" in line:
                self.examine_line(dictionary, line, ":")
            else:
                file.close()
                break
        return dictionary


    def examine_line(self, dictionary, line, splitter):
        strip_chars_start_end_regex = re.compile(r'^(;)+( *)|$\n')
        striped_line = strip_chars_start_end_regex.sub('', line)
        try:
            key, value = striped_line.split(splitter)
            if key in dictionary.keys():
                dictionary[key] = value.strip()
        finally:
            return

    ##~~ AssetPlugin mixin AUTO-GENERATED

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/RPLlogger.js"],
            css=["css/RPLlogger.css"],
            less=["less/RPLlogger.less"]
        )

    ##~~ Softwareupdate hook AUTO-GENERATED

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            RPLlogger=dict(
                displayName="Rpllogger Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="NickGaultney",
                repo="OctoPrint-Rpllogger",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/NickGaultney/OctoPrint-Rpllogger/archive/{target_version}.zip"
            )
        )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Rpllogger"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
#__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = RplloggerPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

