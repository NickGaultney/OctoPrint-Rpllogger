# coding=utf-8
from __future__ import absolute_import
import requests
import re
from file_read_backwards import FileReadBackwards

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

class RplloggerPlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.EventHandlerPlugin):

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            url="http://10.147.20.155:3000",
            printer_name=""
        )

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

    ##~~ EventPlugin Mixin

    def on_event(self, event, payload):
        #self._logger.info("*** " + event + " ***")

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
        self._logger.info("********** RPL LOGS => " + "on_print_started")
        # UPDATE STATUS OF PRINTER
        self.update_printer_status(1)
        # CREATE PRINT LOGS
        self.create_print_log(payload)

    def on_print_stopped(self, payload):
        self._logger.info("********** RPL LOGS => " + "on_print_stopped")
        self.update_printer_status(0)

    def on_print_done(self, payload):
        self._logger.info("********** RPL LOGS => " + "on_print_done")
        self.update_printer_status(2)


    ##~~ Helper Methods

    def get_url(self):
        return self._settings.get(["url"])

    def get_api_path(self):
        return self._settings.get(["url"]) + "/api/v1/"

    def get_printer_name(self):
        return self._settings.get(["printer_name"])

    def get_file_path(self):
        return "/home/pi/.octoprint/uploads/"

    def create_printer(self):
        # Create Printer if_not_exists
        url = self.get_api_path() + "printers_api"
        name = self.get_printer_name()
        payload = {"name" : self.get_printer_name(), "status" : "0"}
        result = requests.post(url, data = payload)
        self._logger.info("********** RPL LOGS => " + "Printer Created: " + name)

    # Status Chart:
    # 0 = Idle
    # 1 = Printing
    # 2 = PrintDone
    def update_printer_status(self, status):
        self._logger.info("********** RPL LOGS => " + "update_printer_status")
        name = self.get_printer_name()
        url = self.get_api_path() + "printers_api/edit"
        payload = {"name" : name, "status" : str(status)}
        result = requests.post(url, data = payload)
        self._logger.info("********** RPL LOGS => " + "Post Result: " + result.text)
        self._logger.info("********** RPL LOGS => " + "Printer Status updated to: " + str(status))

    def create_print_log(self, payload):
        self._logger.info("********** RPL LOGS => " + "create_print_log")
        url = self.get_api_path() + "print_logs_api"
        name = self.get_printer_name()
        metadata = self.find_meta_data(payload["path"], 'Build time', 'Plastic weight')
        payload = { "printer" : name, 
                    "file_name" : payload["name"], 
                    "status" : "1", 
                    "print_time" : metadata["Build time"],
                    "filament_weight" : "Plastic weight"}
        result = requests.post(url, data = payload)
        self._logger.info("********** RPL LOGS => " + "Post Result: " + result.text)
        self._logger.info("********** RPL LOGS => " + "Printer Status updated to: 1")


    ##~~ Extract Meta Data

    def find_meta_data(self, path, *args):
        # initial setup
        self._logger.info("********** RPL LOGS => " + "Path: " + path)
        path = self.get_file_path() + path
        dictionary = dict()
        for arg in args:
            dictionary[arg] = ""

        # read_file_line_by_line()
        with open(path) as file:
            for line in file:
                if line.startswith(";"):
                    examine_line(dictionary, line, ",")
                else:
                    file.close()
                    break

        # self.__reverse_read_file()
        file = FileReadBackwards(path)
        for line in file:
            if line.startswith(";") and ":" in line:
                examine_line(dictionary, line, ":")
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

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/RPLlogger.js"],
            css=["css/RPLlogger.css"],
            less=["less/RPLlogger.less"]
        )

    ##~~ Softwareupdate hook

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

