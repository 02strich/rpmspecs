Name:           strongswan
Version:        5.1.3 
Release:        2
%define         upstream_version   %{version}
%define         strongswan_docdir  %{_docdir}/%{name}
%define         strongswan_libdir  %{_libdir}/ipsec
%define         strongswan_plugins %{strongswan_libdir}/plugins
License:        GPLv2+
Group:          Productivity/Networking/Security
Summary:        OpenSource IPsec-based VPN Solution
Url:            http://www.strongswan.org/
AutoReqProv:    on
Source0:        http://download.strongswan.org/strongswan-%{upstream_version}.tar.bz2
Source1:        http://download.strongswan.org/strongswan-%{upstream_version}.tar.bz2.sig
Source2:        %{name}.init
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  bison flex gmp-devel gperf pkgconfig
BuildRequires:  libcap-devel
BuildRequires:  openssl-devel
BuildRequires:  openldap-devel
BuildRequires:  curl-devel pam-devel
BuildRequires:  iptables libnl >= 1.1
BuildRequires:  sqlite-devel

%description
StrongSwan is an OpenSource IPsec-based VPN Solution for Linux

* runs both on Linux 2.4 (KLIPS IPsec) and Linux 2.6 (NETKEY IPsec) kernels
* implements both the IKEv1 and IKEv2 (RFC 4306) key exchange protocols
* Fully tested support of IPv6 IPsec tunnel and transport connections
* Dynamical IP address and interface update with IKEv2 MOBIKE (RFC 4555)
* Automatic insertion and deletion of IPsec-policy-based firewall rules
* Strong 128/192/256 bit AES or Camellia encryption, 3DES support
* NAT-Traversal via UDP encapsulation and port floating (RFC 3947)
* Dead Peer Detection (DPD, RFC 3706) takes care of dangling tunnels
* Static virtual IPs and IKEv1 ModeConfig pull and push modes
* XAUTH server and client functionality on top of IKEv1 Main Mode authentication
* Virtual IP address pool managed by IKE daemon or SQL database
* Secure IKEv2 EAP user authentication (EAP-SIM, EAP-AKA, EAP-MSCHAPv2, etc.)
* Optional relaying of EAP messages to AAA server via EAP-RADIUS plugin
* Support of IKEv2 Multiple Authentication Exchanges (RFC 4739)
* Authentication based on X.509 certificates or preshared keys
* Generation of a default self-signed certificate during first strongSwan startup
* Retrieval and local caching of Certificate Revocation Lists via HTTP or LDAP
* Full support of the Online Certificate Status Protocol (OCSP, RCF 2560).
* CA management (OCSP and CRL URIs, default LDAP server)
* Powerful IPsec policies based on wildcards or intermediate CAs
* Group policies based on X.509 attribute certificates (RFC 3281)
* Storage of RSA private keys and certificates on a smartcard (PKCS #11 interface)
* Modular plugins for crypto algorithms and relational database interfaces
* Support of elliptic curve DH groups and ECDSA certificates (Suite B, RFC 4869)
* Optional built-in integrity and crypto tests for plugins and libraries
* Smooth Linux desktop integration via the strongSwan NetworkManager applet


%prep
%setup -q -n %{name}-%{upstream_version}
#sed -e 's|@libexecdir@|%_libexecdir|g'    \
#     < $RPM_SOURCE_DIR/strongswan.init.in \
#     > strongswan.init

%build
%configure \
	--disable-static \
	--enable-integrity-test \
	--with-capabilities=libcap \
	--with-plugindir=%{strongswan_plugins} \
	--with-resolv-conf=%{_localstatedir}/run/strongswan/resolv.conf \
	--enable-smartcard \
	--with-default-pkcs11=%{_libdir}/opensc-pkcs11.so \
        --enable-rdrand \
	--enable-cisco-quirks \
	--enable-openssl \
	--enable-agent \
	--enable-md4 \
	--enable-blowfish \
	--enable-eap-sim \
	--enable-eap-sim-file \
	--enable-eap-simaka-sql \
	--enable-eap-simaka-pseudonym \
	--enable-eap-simaka-reauth \
	--enable-eap-md5 \
	--enable-eap-gtc \
	--enable-eap-aka \
	--enable-eap-radius \
	--enable-eap-identity \
	--enable-eap-mschapv2 \
	--enable-eap-aka-3gpp2 \
	--enable-ha \
	--enable-dhcp \
	--enable-sql \
	--enable-attr-sql \
	--enable-addrblock \
	--enable-sqlite \
	--enable-ldap \
	--enable-curl
make %{?_smp_mflags:%_smp_mflags}

%install
make install DESTDIR=%{buildroot}

# delete unwanted library files
rm -f $RPM_BUILD_ROOT%{strongswan_libdir}/lib{charon,hydra,strongswan,simaka}.so
#rm -f $RPM_BUILD_ROOT%{strongswan_libdir}/*.so
find %{buildroot} -type f -name '*.la' -delete

# install init-script
install -m755 -d              ${RPM_BUILD_ROOT}%{_sysconfdir}/init.d/
install -m755 ${RPM_SOURCE_DIR}/strongswan.init ${RPM_BUILD_ROOT}%{_sysconfdir}/init.d/ipsec

# create missing config files
cat << EOT > ${RPM_BUILD_ROOT}%{_sysconfdir}/ipsec.secrets
#
# ipsec.secrets
#
# This file holds the RSA private keys or the PSK preshared secrets for
# the IKE/IPsec authentication. See the ipsec.secrets(5) manual page.
#
EOT

# install documentation
install -m755 -d ${RPM_BUILD_ROOT}%{strongswan_docdir}/
install -m644 TODO NEWS README COPYING ${RPM_BUILD_ROOT}%{strongswan_docdir}/

# fix location of templates
mv ${RPM_BUILD_ROOT}/usr/share/strongswan/* ${RPM_BUILD_ROOT}%{strongswan_docdir}
rmdir ${RPM_BUILD_ROOT}/usr/share/strongswan

install -m755 -d $RPM_BUILD_ROOT%{_localstatedir}/run/strongswan

# fix config permissions
#chmod 644 %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf

# protect configuration from ordinary user's eyes
#chmod 700 %{buildroot}%{_sysconfdir}/%{name}

%post
%{run_ldconfig}
test -d %{_localstatedir}/run/strongswan || %{__mkdir_p} %{_localstatedir}/run/strongswan

%preun
%{stop_on_removal ipsec}
if test -s %{_sysconfdir}/ipsec.secrets.rpmsave; then
  cp -p --backup=numbered %{_sysconfdir}/ipsec.secrets.rpmsave %{_sysconfdir}/ipsec.secrets.rpmsave.old
fi
if test -s %{_sysconfdir}/ipsec.conf.rpmsave; then
  cp -p --backup=numbered %{_sysconfdir}/ipsec.conf.rpmsave %{_sysconfdir}/ipsec.conf.rpmsave.old
fi

%postun
%{run_ldconfig}

%files
%defattr(-,root,root)

%config(noreplace) %attr(600,root,root) %{_sysconfdir}/ipsec.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/ipsec.secrets
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.conf
%dir %{_sysconfdir}/strongswan.d
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/pool.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/starter.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/tools.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon-logging.conf
%dir %{_sysconfdir}/strongswan.d/charon
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/addrblock.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/aes.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/agent.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/attr.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/attr-sql.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/blowfish.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/cmac.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/constraints.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/curl.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/des.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/dhcp.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/dnskey.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-aka-3gpp2.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-aka.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-gtc.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-identity.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-md5.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-mschapv2.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-radius.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-simaka-pseudonym.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-simaka-reauth.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-simaka-sql.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-sim.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/eap-sim-file.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/fips-prf.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/gmp.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/ha.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/hmac.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/kernel-netlink.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/ldap.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/md4.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/md5.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/nonce.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/openssl.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pem.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pgp.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pkcs12.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pkcs1.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pkcs7.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pkcs8.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/pubkey.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/random.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/rc2.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/rdrand.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/resolve.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/revocation.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/sha1.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/sha2.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/socket-default.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/sql.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/sqlite.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/sshkey.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/stroke.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/updown.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/x509.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/xauth-generic.conf
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/strongswan.d/charon/xcbc.conf
%dir %{_sysconfdir}/ipsec.d
%dir %{_sysconfdir}/ipsec.d/crls
%dir %{_sysconfdir}/ipsec.d/reqs
%dir %{_sysconfdir}/ipsec.d/certs
%dir %{_sysconfdir}/ipsec.d/acerts
%dir %{_sysconfdir}/ipsec.d/aacerts
%dir %{_sysconfdir}/ipsec.d/cacerts
%dir %{_sysconfdir}/ipsec.d/ocspcerts
%dir %attr(700,root,root) %{_sysconfdir}/ipsec.d/private
%config %{_sysconfdir}/init.d/ipsec

%{_sbindir}/ipsec
%{_bindir}/pki
%{_mandir}/man8/ipsec.8*
%{_mandir}/man5/ipsec.conf.5*
%{_mandir}/man5/ipsec.secrets.5*
%{_mandir}/man5/strongswan.conf.5*

%dir %{_libexecdir}/ipsec
%dir %{_libexecdir}/ipsec/pool
%{_libexecdir}/ipsec/_updown
%{_libexecdir}/ipsec/_updown_espmark
%{_libexecdir}/ipsec/_copyright
%{_libexecdir}/ipsec/scepclient
%{_libexecdir}/ipsec/starter
%{_libexecdir}/ipsec/stroke
%{_libexecdir}/ipsec/charon

%dir %{strongswan_libdir}
%{strongswan_libdir}/libchecksum.so
%{strongswan_libdir}/libhydra.so.0
%{strongswan_libdir}/libhydra.so.0.0.0
%{strongswan_libdir}/libcharon.so.0
%{strongswan_libdir}/libcharon.so.0.0.0
%{strongswan_libdir}/libstrongswan.so.0
%{strongswan_libdir}/libstrongswan.so.0.0.0
%{strongswan_libdir}/libsimaka.so.0
%{strongswan_libdir}/libsimaka.so.0.0.0
%{strongswan_libdir}/libradius.so
%{strongswan_libdir}/libradius.so.0
%{strongswan_libdir}/libradius.so.0.0.0

%dir %{strongswan_plugins}
%{strongswan_plugins}/libstrongswan-stroke.so
%{strongswan_plugins}/libstrongswan-updown.so
%{strongswan_plugins}/libstrongswan-addrblock.so
%{strongswan_plugins}/libstrongswan-aes.so
%{strongswan_plugins}/libstrongswan-agent.so
%{strongswan_plugins}/libstrongswan-attr.so
%{strongswan_plugins}/libstrongswan-attr-sql.so
%{strongswan_plugins}/libstrongswan-blowfish.so
%{strongswan_plugins}/libstrongswan-constraints.so
%{strongswan_plugins}/libstrongswan-curl.so
%{strongswan_plugins}/libstrongswan-des.so
%{strongswan_plugins}/libstrongswan-dhcp.so
%{strongswan_plugins}/libstrongswan-dnskey.so
%{strongswan_plugins}/libstrongswan-eap-aka-3gpp2.so
%{strongswan_plugins}/libstrongswan-eap-aka.so
%{strongswan_plugins}/libstrongswan-eap-gtc.so
%{strongswan_plugins}/libstrongswan-eap-identity.so
%{strongswan_plugins}/libstrongswan-eap-md5.so
%{strongswan_plugins}/libstrongswan-eap-mschapv2.so
%{strongswan_plugins}/libstrongswan-eap-radius.so
%{strongswan_plugins}/libstrongswan-eap-simaka-pseudonym.so
%{strongswan_plugins}/libstrongswan-eap-simaka-reauth.so
%{strongswan_plugins}/libstrongswan-eap-simaka-sql.so
%{strongswan_plugins}/libstrongswan-eap-sim-file.so
%{strongswan_plugins}/libstrongswan-eap-sim.so
#%{strongswan_plugins}/libstrongswan-farp.so
%{strongswan_plugins}/libstrongswan-fips-prf.so
%{strongswan_plugins}/libstrongswan-gmp.so
%{strongswan_plugins}/libstrongswan-ha.so
%{strongswan_plugins}/libstrongswan-hmac.so
%{strongswan_plugins}/libstrongswan-kernel-netlink.so
%{strongswan_plugins}/libstrongswan-ldap.so
%{strongswan_plugins}/libstrongswan-md4.so
%{strongswan_plugins}/libstrongswan-md5.so
%{strongswan_plugins}/libstrongswan-openssl.so
%{strongswan_plugins}/libstrongswan-pem.so
%{strongswan_plugins}/libstrongswan-pgp.so
%{strongswan_plugins}/libstrongswan-pkcs1.so
%{strongswan_plugins}/libstrongswan-pubkey.so
%{strongswan_plugins}/libstrongswan-random.so
%{strongswan_plugins}/libstrongswan-resolve.so
%{strongswan_plugins}/libstrongswan-revocation.so
%{strongswan_plugins}/libstrongswan-sha1.so
%{strongswan_plugins}/libstrongswan-sha2.so
%{strongswan_plugins}/libstrongswan-socket*.so
%{strongswan_plugins}/libstrongswan-sql.so
%{strongswan_plugins}/libstrongswan-x509.so
%{strongswan_plugins}/libstrongswan-xauth-generic.so
%{strongswan_plugins}/libstrongswan-xcbc.so
%{strongswan_plugins}/libstrongswan-sqlite.so
%{strongswan_plugins}/libstrongswan-cmac.so
%{strongswan_plugins}/libstrongswan-nonce.so
%{strongswan_plugins}/libstrongswan-pkcs12.so
%{strongswan_plugins}/libstrongswan-pkcs7.so
%{strongswan_plugins}/libstrongswan-pkcs8.so
%{strongswan_plugins}/libstrongswan-rc2.so
%{strongswan_plugins}/libstrongswan-rdrand.so
%{strongswan_plugins}/libstrongswan-sshkey.so

%dir %{strongswan_docdir}
%{strongswan_docdir}/TODO
%{strongswan_docdir}/NEWS
%{strongswan_docdir}/README
%{strongswan_docdir}/COPYING
%{strongswan_docdir}/templates/config/plugins/*.conf
%{strongswan_docdir}/templates/config/strongswan.conf
%{strongswan_docdir}/templates/config/strongswan.d/charon-logging.conf
%{strongswan_docdir}/templates/config/strongswan.d/charon.conf
%{strongswan_docdir}/templates/config/strongswan.d/pool.conf
%{strongswan_docdir}/templates/config/strongswan.d/starter.conf
%{strongswan_docdir}/templates/config/strongswan.d/tools.conf
%{strongswan_docdir}/templates/database/sql/mysql.sql
%{strongswan_docdir}/templates/database/sql/sqlite.sql
%{_mandir}/man1/pki.1*
%{_mandir}/man1/pki---acert.1*
%{_mandir}/man1/pki---gen.1*
%{_mandir}/man1/pki---issue.1*
%{_mandir}/man1/pki---keyid.1*
%{_mandir}/man1/pki---pkcs7.1*
%{_mandir}/man1/pki---print.1*
%{_mandir}/man1/pki---pub.1*
%{_mandir}/man1/pki---req.1*
%{_mandir}/man1/pki---self.1*
%{_mandir}/man1/pki---signcrl.1*
%{_mandir}/man1/pki---verify.1*
%{_mandir}/man8/_updown.8*
%{_mandir}/man8/_updown_espmark.8*
%{_mandir}/man8/scepclient.8*

%dir %ghost %{_localstatedir}/run/strongswan

%changelog
