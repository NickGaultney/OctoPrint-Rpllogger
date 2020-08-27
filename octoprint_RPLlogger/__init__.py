# coding=utf-8
from __future__ import absolute_import
import requests

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

	def on_event(event, payload):
		if event == "PrintStarted":
			on_print_started(payload)
		elif event == "PrintFailed" or event == "PrintCancelled":
			on_print_stopped(payload)
		elif event == "PrintDone":
			on_print_done(payload)
		elif event == "Startup"
			on_startup()

	def on_print_started(payload):
		# UPDATE STATUS OF PRINTER
		# ADD TO PRINT LOGS
		x=5

	def on_print_stopped(payload):
		# Blah
		x=5

	def on_print_done(payload):
		# Blah
		x=5

	def on_startup():
		# Create Printer if_not_exists
		url = get_url + get_api_path + "printers_api"
		name = get_printer_name()
		if not name == "":
			payload = {"name" : get_printer_name(), "status" : "0"}
			result = requests.post(url, data = payload)

	##~~ Helper Methods

	def get_url():
		self._settings.get(["url"])

	def get_api_path():
		"/api/v1/"

	def get_printer_name():
		self._settings.get(["printer_name"])

	# Status Chart:
	# 0 = Idle
	# 1 = Printing
	# 2 = PrintDone
	def update_printer_status():
		# Blah
		x=5

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

