# What is Odoo?

Odoo is a suite of business management software tools including (but not limited to):

- CRM
- Billing
- Accounting
- Manufacturing
- Project management

ConversionLogix is using Odoo to replace a handful of other apps and services to help run our business.

Odoo offers an open-source community edition as well as a paid managed enterprise edition. We use the paid enterprise edition.

This is important to note because it impacts our development efforts in the following ways:

- Odoo hosts our instance(s)
- Odoo prescribes the server environments (described in the next section)
- Odoo prescribes how we branch/merge/deploy

<br/>
<br/>

# Before you start working

Odoo is a third-party application with existing detailed documentation. This README is not intended to cover it but you can [Read the Odoo documentation at their site](https://www.odoo.com/documentation/14.0/developer/howtos/rdtraining/01_architecture.html).

In terms of developing for our instance, it's important to know that Odoo is built on the concept of extension by way of custom modules, also referred to as "addons".

These modules are typically a "front-to-bacK" unit of functionality and are organized as such.

Odoo comes with a core selection of modules, which _SHOULD_ live in the "addons" directory.

Since we are using the enterprise version, you'll also need a collection of enterprise modules. Getting those is covered in the next section.

Any customizations that we develop will live in their own directory. By convention, we have named that "clx-addons". Getting those modules is convered in the next section as well.

The vast majority of development that you would do in our instance of Odoo is going to happen in the "clx-addons" directory.

## Odoo.sh

As part of the enterprise offering, Odoo gives us a hosted environment at odoo.sh that allows us to manage our instances. This includes:

- Git repo
- Deployments
- Database backups
- Logs
- & more

This is important to note because we periodically pull database backups from here to set up locally.

<br/>
<br/>

# How to get set up locally

This README is focused on getting your local environment set up on a Mac. If you are in a situation where you are not using a Mac, here are a couple of links for other operating systems:

- [Install Odoo on Windows](https://www.odoo.com/documentation/14.0/administration/install/install.html#id4)
- [Install Odoo on Linux](https://www.odoo.com/documentation/14.0/administration/install/install.html#id7)

Like many third-party application installations, your experience may not be as smooth as the documentation claims. If you experience an issue that needs to make it into this document to help others, please include it.

<br/>

## Get the code:

### Clone Odoo

First, clone the Odoo community edition to your machine and cd into that branch:

```
$ git clone https://github.com/odoo/odoo.git
cd ./odoo
```

We are using version 13, so make sure you checkout the 13.0 branch:

```
git checkout 13.0
```

### Clone Odoo enterprise modules

Since we're an enterprise customer, clone our repo containing the enterprise modules into your new Odoo project directory. It's recommended to name the directory "enterprise":

```
git clone https://github.com/adsupnow/odoo_enterprise.git enterprise
```

### Clone custom CLX modules

Clone our custom modules into a directory named "clx-addons":

```
git clone https://github.com/adsupnow/odoo.git clx-addons
```

Checkout our "staging" branch. This is our development trunk:

```
git checkout staging
```

When you've checked out the above 3 repos/branches, your project structure should include these directories in the root:

- addons (Odoo core modules)
- clx-addons (CLX custom modules)
- enterprise (Odoo enteprise modules)

## Install Python and PostgreSQL

Odoo is developed in Python and runs on a PostgreSQL database. You'll need both installed on your machine.

One thing to note, our team faced multilple issues running Odoo on the latest version of Python. To get around that, we've installed Pyenv and use a lower version of Python.

You may need to experiment with the version that works on your machine but 3.7.10 seems to work for us.

This link walks through the installation and setup of Pyenv:
https://realpython.com/intro-to-pyenv/

**Note**: When trying to install another version of Python, depending on your machine, you may run into some common known issues.

Each machine is a little different but here are some links to troubleshoot:

- https://github.com/pyenv/pyenv/wiki/Common-build-problems
- https://github.com/pyenv/pyenv/issues/1184
- https://www.gitmemory.com/issue/pyenv/pyenv/1184/458358654

If you continue to have issues, you can uninstall pyenv and try installing it via Homebrew.

Once Python is installed, you'll need to install PostgreSQL.

You can install it in various ways which are listed on the PostgreSQL site at the following link:  
https://www.postgresql.org/download/macosx/

The easiest way to install it is via PostgresApp:  
https://postgresapp.com/

## Restore staging database to local

Once you've completed the previous steps, you'll need to restore a copy of our staging database to your machine.

It's important to make sure you pull a staging copy because everything is stored in the database in Odoo. Our staging database _should_ be the latest representation of all non-live development efforts.

The quickest way to restore a copy of the staging database is to create a database from a database dump file.

To take a backup of the staging database:

- Log into odoo.sh
- Click "Branches" in the top navigation menu
- Under the "Staging" section in the left sidebar menu, click the "staging" menu item
- In the main content section, click the "Backups" menu item
- If the list of backups contains a very recent staging backup, click the "Download" button next to it
- If there is not a refcent staging backup, click the "Create Backup" button (Note, it will take several minutes to create the backup)
- When the backup is complete, click the notification at the top right
- Click "Go to backup"
- Click "Download" to download the zip file to your machine

Once you have the zip file downloaded, unzip it and cd into the unzipped directory. It helps to extract it close to your odoo development directory.

Once inside the unzipped directory, run the following command in a terminal:

```
createdb -O odoo [new_database_name]
psql [new_database_name] < dump.sql
```

To verify that your database has been created, you can use the Postgres.app UI or a tool like one of the following to connect to your local instance of PostgreSQL and view your database:

- [pgAdmin](https://www.pgadmin.org/)
- [DBeaver](https://dbeaver.io/)

## Odoo.conf

To connect your application to your database and run Odoo, you'lll need to fill out your odoo.conf file. The default location for this file is in the "debian" folder in the root of the project directory.

The minimum config values needed are the following:

```
[options]
addons_path = /Users/your-machine-username/Work/clsp/odoo/addons,/Users/your-machine-username/Work/clsp/odoo/enterprise,/Users/your-machine-username/Work/clsp/odoo/clx-addons
admin_passwd = $pbkdf2-sha512$25000$CYEQYkzJWStFaC1lrFUqxQ$rLX4PNxyC2sKirbDNc0ARKqXA9u17/qea2TTQkk0/m6thSVTOzanJnkX0S.AcmOv6gYS68ePM3Rx6g7HdD4STQ
data_dir = /Users/your-machine-username/Library/Application Support/Odoo
db_host = localhost
db_maxconn = 64
db_name = False
db_password = odoo
db_port = 5432
db_sslmode = prefer
db_template = template1
db_user = odoo
http_enable = True
http_interface =
http_port = 8069
```

TODO: Add an example conf file with all of the possible values. Explain what they are used for.

## Running Odoo

To run Odoo for local testing, run the following in a terminal (given that the conf is in the debian directory):

```
./odoo-bin --conf ./debian/odoo.conf
```

If everything is wired up correctly, you should be able to view the Odoo instance in your browser at the following URL:

```
https://localhost:8069
```

Clicking the apps icon in the top left corner will take you to the Odoo landing page of all Apps & Modules, typically at this address:

```
http://localhost:8069/web#cids=1&home=
```

If things aren't working as expected, consult with the team and revisit this document to make any needed updates.

<br/>
<br/>

# Our branching strategy

As noted in an earlier section, Odoo enterprise is a managed solution and prescribes some of our branching strategy.

Our branch structure is as follows:

- **production**
  - Represents what is live at all times
- **staging**
  - Collection of work that has been approved for release to production. Also used as our development trunk
- **qa** (may be named with a date suffix)
  - This is our dedicated QA verification environment
- **dev staging branches**
  - These are dedicated dev branches used for feature testing and demoes before going to QA
- **feature branches**
  - These are the branches that contain dev feature work

When you need to contribute to the application, the process is as follows:

- Pull the latest from **staging**
- Cut a new branch with the following naming convention
  - Jira ticket Id - short descriptor of intent, e.g. CLXD-1234-fix-login
- When you're ready to test on a real instance, merge to your developer staging branch
- Once testing is done on your developer testing branch, open a Pull Request to merge into the QA branch
- Once QA approves you work, merge it to staging

# How we release

TODO: Revisit once we decide on release schedules.

This is subject to change but we currently are not releasing on defined schedules.
