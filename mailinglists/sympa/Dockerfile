FROM alpine:3.8

RUN apk add --no-cache openrc rsyslog python py-jinja2 gcc g++ make perl perl-class-singleton perl-encode-locale perl-dev perl-datetime perl-uri perl-dbi perl-xml-libxml perl-html-parser perl-mime-charset curl wget perl-unicode-linebreak perl-file-copy-recursive perl-term-progressbar perl-http-message perl-io-stringy perl-lwp-useragent-determined perl-regexp-common-net-cidr perl-cgi perl-template-toolkit perl-html-tree perl-mime-tools perl-html-formattext-withlinks-andtables perl-dbd-sqlite perl-dbd-mysql perl-dbd-pg perl-email-address apache2 libxml2-dev apache2-utils apache2-proxy apache-mod-fcgid perl-archive-zip perl-cgi-fast perl-datetime spawn-fcgi postfix postfix-sqlite postfix-pcre patch

RUN curl -L http://xrl.us/cpanm > /bin/cpanm && chmod +x /bin/cpanm
RUN cpanm Mail::Address HTML::StripScripts::Parser Net::CIDR File::NFSLock MHonArc::UTF8 MIME::EncWords Locale::Messages DateTime::Format::Mail

RUN mkdir /patches
COPY patches/mhonarc.patch /patches
RUN patch -p0 -i /patches/mhonarc.patch

RUN cpanm MIME::Lite::HTML --force

RUN addgroup -S sympa
RUN adduser -G sympa -s /sbin/nologin sympa -D

RUN wget https://github.com/sympa-community/sympa/releases/download/6.2.36/sympa-6.2.36.tar.gz 
RUN tar -xzf sympa-6.2.36.tar.gz
RUN rm sympa-6.2.36.tar.gz

RUN cd sympa-6.2.36; ./configure --with-initdir=/etc/init.d --with-spooldir=/data/sympa/spool --with-expldir=/data/sympa/list_data --with-arcdir=/data/sympa/arc 
RUN cd sympa-6.2.36; make
RUN cd sympa-6.2.36; make install

RUN mkdir /etc/mail
RUN chown sympa:sympa /etc/mail

run cp /home/sympa/bin/wwsympa-wrapper.fcgi /var/www/localhost/fcgi-bin

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
RUN rc-update add sympa2 default

EXPOSE 80/tcp

CMD /start.py
