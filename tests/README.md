# How to populate test db


mysqldump -h 127.0.0.1 -u testuser -ptestpassword --no-create-info --skip-triggers --single-transaction --ssl-mode=DISABLED arXiv arXiv_moderators | sed 's/INSERT INTO/INSERT IGNORE INTO/g' | mysql -h 127.0.0.1 -P 21601 -u root -proot_password --ssl-mode=DISABLED --force arXiv 
