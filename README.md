# brew-web
Docker compose for self-hosted brewing. Includes recipes, logs, information, and tools.

Starting off as a self-made project, I want to share so others can use the same utilities I am creating for myself.

= Password Reset =
If you have forgotten your password, delete the file /instance/force_reset.flag and restart your container "docker compose stop" then "docker compose up -d --build" Once you visit your site again, it will prompt you for a password change. If you need to change your password, you can go to your user settings (top right) select "Settings" and the Change Password in the side-bar.

= Updating database with current version =
Updates will happen when I add more variables to the database. If you are downloading fresh, you will not need to worry about this. If you have a later version and wish to update or pull the current version, follow these commands. (results may vary if you are using somthing else other than Ubuntu Server)
  1. run docker exec -it brew-web /bin/sh
  2. export FLASK_APP=app
  3. export FLASK_ENV=development
  4. flask db migrate -m "Upgrade version"
  5. flask db upgrade
  6. exit
  7. once in the directory, run docker compose down
  8. then docker compose up -d --build
