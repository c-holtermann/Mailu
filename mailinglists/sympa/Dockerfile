FROM alpine:3.11

RUN apk add --no-cache openrc rsyslog python3 py3-jinja2 py3-pip gcc g++ make perl perl-class-singleton perl-encode-locale perl-dev perl-datetime perl-uri perl-dbi perl-xml-libxml perl-html-parser perl-mime-charset curl wget perl-unicode-linebreak perl-file-copy-recursive perl-term-progressbar perl-http-message perl-io-stringy perl-lwp-useragent-determined perl-regexp-common-net-cidr perl-cgi perl-template-toolkit perl-html-tree perl-mime-tools perl-html-formattext-withlinks-andtables perl-dbd-sqlite perl-dbd-mysql perl-dbd-pg perl-dbd-odbc perl-email-address apache2 libxml2-dev apache2-utils apache2-proxy apache-mod-fcgid perl-archive-zip perl-cgi-fast perl-datetime spawn-fcgi postfix postfix-sqlite postfix-pcre patch openssl openssl-dev unixodbc unixodbc-dev perl-net-ssleay perl-io-socket-ssl perl-crypt-openssl-rsa perl-crypt-eksblowfish perl-datetime-format-mail perl-net-cidr perl-clone perl-mail-dkim

RUN pip3 install socrate

RUN curl -L http://xrl.us/cpanm > /bin/cpanm && chmod +x /bin/cpanm
RUN cpanm Mail::Address HTML::StripScripts::Parser File::NFSLock MHonArc::UTF8 MIME::EncWords Locale::Messages Crypt::CipherSaber Data::Password
RUN cpanm Math::Base::Convert MIME::Lite::HTML --force
RUN cpanm Crypt::SMIME DBD::CSV  Net::DNS Net::LDAP 

RUN addgroup -S sympa
RUN adduser -G sympa -s /sbin/nologin sympa -D

ENV sympa_version=6.2.60

RUN wget https://github.com/sympa-community/sympa/releases/download/$sympa_version/sympa-$sympa_version.tar.gz 
RUN tar -xzf sympa-$sympa_version.tar.gz
RUN rm sympa-$sympa_version.tar.gz

RUN cd sympa-$sympa_version; ./configure --with-initdir=/etc/init.d --with-spooldir=/data/sympa/spool --with-expldir=/data/sympa/list_data
RUN cd sympa-$sympa_version; make
RUN cd sympa-$sympa_version; make install

RUN mkdir /etc/mail
RUN chown sympa:sympa /etc/mail

RUN cp /home/sympa/bin/wwsympa-wrapper.fcgi /var/www/localhost/fcgi-bin

RUN mv /etc/apache2/conf.d/proxy.conf /etc/apache2/conf.d/proxy.conf.package
COPY conf /conf
COPY start.py /start.py

RUN mkdir -p /tmp/overrides
COPY overrides/* /tmp/overrides/

# Disable getty's
RUN sed -i 's/^\(tty\d\:\:\)/#\1/g' /etc/inittab \
	&& sed -i \
        # Change subsystem type to "docker"
        -e 's/#rc_sys=".*"/rc_sys="docker"/g' \
        # Allow all variables through
        -e 's/#rc_env_allow=".*"/rc_env_allow="\*"/g' \
        # Start crashed services
        -e 's/#rc_crashed_stop=.*/rc_crashed_stop=NO/g' \
        -e 's/#rc_crashed_start=.*/rc_crashed_start=YES/g' \
        # Define extra dependencies for services
        -e 's/#rc_provide=".*"/rc_provide="loopback net"/g' \
        /etc/rc.conf \
    	# Remove unnecessary services
    	&& rm -f /etc/init.d/hwdrivers \
            /etc/init.d/hwclock \
            /etc/init.d/hwdrivers \
            /etc/init.d/modules \
            /etc/init.d/modules-load \
            /etc/init.d/modloop \
	# Can't do cgroups
    	&& sed -i 's/\tcgroup_add_service/\t#cgroup_add_service/g' /lib/rc/sh/openrc-run.sh \
	&& sed -i 's/VSERVER/DOCKER/Ig' /lib/rc/sh/init.sh

# Apache log to docker
RUN sed -i -r 's@Errorlog .*@Errorlog /proc/1/fd/1@i' /etc/apache2/httpd.conf

COPY init.d/* /etc/init.d/
RUN rc-update add rsyslog
RUN rc-update add apache2 boot
RUN rc-update add postfix boot
RUN rc-update add wwsympa default
RUN rc-update add sympa default

EXPOSE 80/tcp

CMD /start.py
