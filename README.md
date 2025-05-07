Brew-Web v1.2.0 – Self-Hosted Brewing Dashboard
Brew-Web is a self-hosted utility for managing mead, wine, and beer batches. It includes:

Recipe creation and scaling

Batch tracking and gravity logging

Yeast database reference

Brewing calculators (ABV, dilution, TOSNA, etc.)

Role-based user access and admin controls

Originally created for personal use, Brew-Web is now shared for others in the homebrewing community.

🔧 Installation Instructions (Ubuntu or similar)
  1. Download and unzip the latest release

bash: cd ~
bash: curl -L -o brew-web-v1.2.0.zip https://github.com/anndrox/brew-web/raw/main/brew-web-v1.2.0.zip
bash: unzip brew-web-v1.2.0.zip
bash: cd brew-web

  3. Start the container

bash: docker compose up -d --build

Visit http://your-server-ip:4452 to access the app.

🔐 Password Reset
If you've forgotten your password:

bash: rm instance/force_reset.flag
bash: docker compose stop
bash: docker compose up -d --build

Now, visiting the site will prompt you to create a new admin account.

To change your password manually:

Click your profile icon (top right)

Go to Settings → Change Password

🔄 Updating the Database (for existing installs)
If you are upgrading from a previous version and need to apply database schema changes:

bash: docker exec -it brew-web /bin/sh
bash: export FLASK_APP=app
bash: export FLASK_ENV=development
bash: flask db migrate -m "Upgrade version"
bash: flask db upgrade
bash: exit
(or CTRL+D and then exit)
bash: docker compose down
bash: docker compose up -d --build

👥 User Roles & Permissions
Brew-Web supports role-based access control to manage what users can see and do:

Role	Description	Permissions
admin    --   Full access to the system	Create/edit/delete users, recipes, batches; access admin dashboard
editor   --   Power user for day-to-day brewing	Create/edit batches and recipes, view all data
user	   --   Read-only access	View recipes, batches, calculators; no editing

The first user created during /setup is automatically made an admin.

Admins can create, delete, or reset passwords for any user from the Administration page under Settings.

📁 File Structure Summary
/app/ – Flask source code

/instance/ – Configuration and password reset flag

/static/ – Images, styles, favicon

/templates/ – HTML templates

docker-compose.yml – Defines how Brew-Web runs
