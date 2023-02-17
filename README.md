# McStatusArchive
### This program was made to grab and save some info from mc servers
<details>
<summary>Java Saved data</summary>
    save_time<br>
    players_on <br>
    players_max <br>
    ping <br>
    players_sample <br>
    version_protocol <br>
    version_name <br>
    motd <br>
    favicon
</details>

<details>
<summary>Bedrock Saved data</summary>
    save_time <br>
    players_on <br>
    players_max <br>
    ping <br>
    version_protocol <br>
    version_name <br>
    version_brand <br>
    motd <br>
    gamemode <br>
    map
</details>

# Requirements
- mcstatus (pip install mcstatus)
- Python with a version of sqlite that supports serialized mode
  - (See [DbManager.py](database/DbManager.py#16) or just launch the program for more info)

# Info
The DB saves `save_time` as unix time **from your timezone**  
(eg. mine is in UTC+1, Central European Standard Time)  