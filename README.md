# Fresh Intellivent Sky integration for Home Asssistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

_Component to integrate with [fresh_intellivent_sky][fresh_intellivent_sky]._

**This component will set up the following platforms.**

Note! This component is in a very early stage so breaking changes and bugs are to be expected.

Platform | Description
-- | --
`binary_sensor` | Show something `True` or `False`.
`sensor` | Show info from blueprint API.
`switch` | Switch something `True` or `False`.

## HACS Installation

1. Go to HACS in Home Assistant
2. Click on integrations
3. In top right corner, click three dots, click 'Custom repositories'
4. Paste this repository URL (https://github.com/angoyd/freshintelliventHacs) in repository box
5. Choose integration in category box
6. Click add, wait while repository is added, close window
7. Click the new repository, and click download
8. Restart Home Assistant
9. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Fresh Intellivent Sky"
10. The integration will scan for fans and then ask for your authcode.


## Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `fresh_intellivent_sky`.
4. Download _all_ the files from the `custom_components/fresh_intellivent_sky/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Fresh Intellivent Sky"
8. The integration will scan for fans and then ask for your authcode.


## Configuration is done in the UI

<!---->

***

[fresh_intellivent_sky]: https://github.com/angoyd/freshintelliventHacs
[commits-shield]: https://img.shields.io/github/commit-activity/y/angoyd/freshintelliventHacs.svg?style=for-the-badge
[commits]: https://github.com/angoyd/freshintelliventHacs/commits/master
[hacs]: https://github.com/custom-components/hacs
[license-shield]: https://img.shields.io/github/license/angoyd/freshintelliventHacs.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/angoyd/freshintelliventHacs.svg?style=for-the-badge
[releases]: https://github.com/angoyd/freshintelliventHacs/releases
