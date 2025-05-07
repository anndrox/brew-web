Brew-Web v1.2.0 – Self-Hosted Brewing Dashboard
Brew-Web is a self-hosted utility for managing mead, wine, and beer batches. It includes:

- Recipe creation and scaling

- Batch tracking and gravity logging

- Yeast database reference

- Brewing calculators (ABV, dilution, TOSNA, etc.)

- Role-based user access and admin controls

Originally created for personal use, Brew-Web is now shared for others in the homebrewing community.

🔧 Installation Instructions (Ubuntu or similar)
  1. Download and unzip the latest release

<code> cd ~
<code> curl -L -o brew-web-v1.2.0.zip https://github.com/anndrox/brew-web/raw/main/brew-web-v1.2.0.zip
<code> unzip brew-web-v1.2.0.zip
<code> cd brew-web
  3. Start the container

<code> docker compose up -d --build

Visit http://<your-server-ip>:4452 to access the app.

🔐 Password Reset
If you've forgotten your password:

<code> rm instance/force_reset.flag
<code> docker compose stop
<code> docker compose up -d --build

Now, visiting the site will prompt you to create a new admin account.

To change your password manually:

Click your profile icon (top right)

Go to Settings → Change Password

🔄 Updating the Database (for existing installs)
If you are upgrading from a previous version and need to apply database schema changes:

While the container is running:
<code> docker exec -it brew-web /bin/sh
<code> export FLASK_APP=app
<code> export FLASK_ENV=development
<code> flask db migrate -m "Upgrade version"
<code> flask db upgrade
<code> exit
<code> docker compose down
<code> docker compose up -d --build


📁 File Structure Summary
/app/ – Flask source code

/instance/ – Configuration and password reset flag

/static/ – Images, styles, favicon

/templates/ – HTML templates

docker-compose.yml – Defines how Brew-Web runs
