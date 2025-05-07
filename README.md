Brew-Web v1.2.0 – Self-Hosted Brewing Dashboard
Brew-Web is a self-hosted utility for managing mead, wine, and beer batches. It includes:

Recipe creation and scaling

Batch tracking and gravity logging

Yeast database reference

Brewing calculators (ABV, dilution, TOSNA, etc.)

Role-based user access and admin controls

Originally created for personal use, Brew-Web is now shared for others in the homebrewing community.

🔧 Installation Instructions (Ubuntu or similar)
1. Install Docker and Docker Compose
If not already installed:

bash
Copy
Edit
sudo apt update
sudo apt install -y docker.io docker-compose unzip curl
2. Download and unzip the latest release
bash
Copy
Edit
cd ~
curl -L -o brew-web-v1.2.0.zip https://github.com/anndrox/brew-web/raw/main/brew-web-v1.2.0.zip
unzip brew-web-v1.2.0.zip
cd brew-web
3. Start the container
bash
Copy
Edit
docker compose up -d --build
Visit http://<your-server-ip>:4452 to access the app.

🔐 Password Reset
If you've forgotten your password:

bash
Copy
Edit
rm instance/force_reset.flag
docker compose stop
docker compose up -d --build
Now, visiting the site will prompt you to create a new admin account.

To change your password manually:

Click your profile icon (top right)

Go to Settings → Change Password

🔄 Updating the Database (for existing installs)
If you are upgrading from a previous version and need to apply database schema changes:

bash
Copy
Edit
docker exec -it brew-web /bin/sh
export FLASK_APP=app
export FLASK_ENV=development
flask db migrate -m "Upgrade version"
flask db upgrade
exit
docker compose down
docker compose up -d --build
📁 File Structure Summary
/app/ – Flask source code

/instance/ – Configuration and password reset flag

/static/ – Images, styles, favicon

/templates/ – HTML templates

docker-compose.yml – Defines how Brew-Web runs
