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
  - (See [DbManager.py](database/DbManager.py#13) or just launch the program for more info)

# Info
The DB saves `save_time` as unix time **from your timezone**  
(eg. mine is in UTC+1, Central European Standard Time)  

# HOW THIS WORKS:
- The script grabs every info about the server & saves it to db.
- Next time the save runs, it only saves fields different from the previous saved values.  
 Other unchanged fields are just filled with NULLs.

# TODOs:
docker container containing everything below below  
actual website/UI to view data  
-> to avoid SQL injection, do smth like "if input not in trusted_servers" server side  
other sources (from the internet etc) to view old data  
  
Few servers (see servers_DOWN.txt) are having issues  
See if I can PR or fix the thing or smth  
  
to save even more space, when server is down set playercount to "DOWN"
  
and when the data doesn't change, don't actually save any lines