################################################################
# Filename: parkapi/data_model/table_setup.sql
# Location: /Users/Atom/repos/next/ridecell
# Project :
# Date    : 2017-04-07
# Author  : Atom
# Scope   :
# Usage   :
################################################################

# Parking Slot
create table pslot(psid int primary key not null AUTO_INCREMENT,
                   lat decimal(10,8) not null,
                   lng decimal(11,8) not null);

# Reservations
create table rservation(rid int primary key not null,
                        psid int not null,
                        startts TIMESTAMP not null,
                        endts   TIMESTAMP DEFAULT '1970-01-01 00:00:01')
