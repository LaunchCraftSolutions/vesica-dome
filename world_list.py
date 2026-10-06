"""Domes to look for beyond the first collection: buildings from the same span of time (Roman to the early 1900s) and older.

Each line: the name shown on the desk, the English Wikipedia article (used to look up where the building is), the words to
search Wikimedia Commons with (blank: the article's name and "dome interior"), when it was built, who built it, and a note.
The dates and builders are from general reference knowledge, not from the photos. A blank builder means it has not been
looked up, not that no name has come down.
"""
RAW = """
Rome, St Peter's | St. Peter's Basilica | St. Peter's Basilica dome interior cupola | Dome 1547–90 | Michelangelo, completed by Giacomo della Porta and Domenico Fontana |
Rome, Sant'Ivo alla Sapienza | Sant'Ivo alla Sapienza | Sant'Ivo alla Sapienza cupola interno | 1642–60 | Francesco Borromini |
Rome, San Carlo alle Quattro Fontane | San Carlo alle Quattro Fontane | San Carlo alle Quattro Fontane cupola | 1638–46 | Francesco Borromini | Oval dome
Rome, Sant'Andrea al Quirinale | Sant'Andrea al Quirinale | Sant'Andrea al Quirinale cupola | 1658–70 | Gian Lorenzo Bernini | Oval dome
Rome, Sant'Andrea della Valle | Sant'Andrea della Valle | Sant'Andrea della Valle cupola interno | Dome 1622 | Carlo Maderno; fresco by Giovanni Lanfranco |
Rome, Sant'Agnese in Agone | Sant'Agnese in Agone | Sant'Agnese in Agone cupola interno | 1652–72 | Girolamo and Carlo Rainaldi, and Francesco Borromini |
Rome, Il Gesù | Church of the Gesù | Chiesa del Gesù Roma cupola | 1568–84 | Giacomo Barozzi da Vignola and Giacomo della Porta |
Rome, Santa Costanza | Santa Costanza | Santa Costanza Roma cupola interno | About 340–350 | |
Rome, Santi Luca e Martina | Santi Luca e Martina | Santi Luca e Martina cupola | 1635–64 | Pietro da Cortona |
Rome, Sant'Ignazio | Sant'Ignazio, Rome | Sant'Ignazio Roma finta cupola Pozzo | Painted 1685 | Andrea Pozzo | A flat canvas painted to look like a dome
Rome, Santa Maria degli Angeli | Santa Maria degli Angeli e dei Martiri | Santa Maria degli Angeli Roma cupola vestibolo | Baths 298–306; church 1563–66 | Church by Michelangelo, in the Baths of Diocletian |
Florence, cathedral | Florence Cathedral | Florence Cathedral dome interior fresco Vasari | Dome 1420–36 | Filippo Brunelleschi; frescoes by Giorgio Vasari and Federico Zuccari |
Florence, baptistery | Florence Baptistery | Battistero Firenze cupola mosaico | 1059–1128; mosaics 13th century | |
Florence, Chapel of the Princes | Medici Chapels | Cappella dei Principi cupola | Begun 1604 | Matteo Nigetti |
Florence, Pazzi Chapel | Pazzi Chapel | Cappella dei Pazzi cupola | 1442–78 | Filippo Brunelleschi |
Venice, Santa Maria della Salute | Santa Maria della Salute | Santa Maria della Salute cupola interno | 1631–87 | Baldassare Longhena |
Venice, St Mark's | St Mark's Basilica | Basilica di San Marco cupola mosaico | 1063–94; mosaics 12th–13th centuries | |
Ravenna, San Vitale | Basilica of San Vitale | San Vitale Ravenna cupola | 526–547 | |
Ravenna, Baptistery of Neon | Baptistery of Neon | Battistero Neoniano cupola mosaico | About 400–458 | |
Ravenna, Arian Baptistery | Arian Baptistery | Battistero degli Ariani cupola mosaico | About 500 | Built under Theodoric the Great |
Ravenna, Mausoleum of Galla Placidia | Mausoleum of Galla Placidia | Mausoleo di Galla Placidia cupola stelle | About 425–450 | |
Pisa, baptistery | Pisa Baptistery | Battistero Pisa cupola interno | 1152–1363 | Begun by Diotisalvi |
Parma, baptistery | Parma Baptistery | Battistero di Parma cupola | 1196–1270 | Benedetto Antelami |
Parma, cathedral | Parma Cathedral | Duomo di Parma cupola Correggio | Fresco 1526–30 | Fresco by Antonio da Correggio |
Padua, baptistery | Padua Baptistery | Battistero Padova cupola Giusto de' Menabuoi | Frescoes 1375–78 | Frescoes by Giusto de' Menabuoi |
Siena, cathedral | Siena Cathedral | Duomo di Siena cupola interno | Dome 1259–64 | |
Turin, San Lorenzo | San Lorenzo, Turin | San Lorenzo Torino cupola Guarini | 1668–87 | Guarino Guarini |
Turin, Chapel of the Holy Shroud | Chapel of the Holy Shroud | Cappella della Sindone cupola | 1668–94 | Guarino Guarini |
Turin, Superga | Basilica of Superga | Basilica di Superga cupola interno | 1717–31 | Filippo Juvarra |
Turin, Mole Antonelliana | Mole Antonelliana | Mole Antonelliana interno cupola | 1863–89 | Alessandro Antonelli |
Vicoforte | Sanctuary of Vicoforte | Santuario di Vicoforte cupola | 1596–1733 | Ascanio Vitozzi; dome by Francesco Gallo | Oval dome
Novara, San Gaudenzio | Basilica of San Gaudenzio | San Gaudenzio Novara cupola interno | Dome 1844–78 | Alessandro Antonelli |
Milan, Galleria Vittorio Emanuele II | Galleria Vittorio Emanuele II | Galleria Vittorio Emanuele II cupola | 1865–77 | Giuseppe Mengoni | Glass dome
Milan, Santa Maria delle Grazie | Santa Maria delle Grazie, Milan | Santa Maria delle Grazie Milano tribuna cupola | Tribune 1492–97 | Attributed to Donato Bramante |
Milan, San Vittore in Ciel d'Oro | Basilica of Sant'Ambrogio | San Vittore in Ciel d'Oro cupola mosaico | 5th century | |
Naples, Galleria Umberto I | Galleria Umberto I | Galleria Umberto I Napoli cupola | 1887–90 | Emanuele Rocco | Glass dome
Naples, San Francesco di Paola | San Francesco di Paola, Naples | San Francesco di Paola Napoli cupola interno | 1816–46 | Pietro Bianchi |
Mantua, Sant'Andrea | Basilica of Sant'Andrea, Mantua | Sant'Andrea Mantova cupola | Dome 1732–65 | Dome by Filippo Juvarra |
Todi, Santa Maria della Consolazione | Santa Maria della Consolazione, Todi | Santa Maria della Consolazione Todi cupola interno | 1508–1607 | |
Montepulciano, San Biagio | San Biagio, Montepulciano | San Biagio Montepulciano cupola interno | 1518–45 | Antonio da Sangallo the Elder |
Palermo, Palatine Chapel | Cappella Palatina | Cappella Palatina cupola Pantocratore | 1132–43 | Built for Roger II of Sicily |
Palermo, Martorana | Martorana | Martorana Palermo cupola mosaico | 1143–51 | Built for George of Antioch |
Baiae, Temple of Mercury | Baiae | Tempio di Mercurio Baia cupola | 1st century BC | | A Roman bath hall; the oldest large concrete dome still standing
Mosta | Rotunda of Mosta | Mosta Rotunda dome interior | 1833–60 | Giorgio Grognet de Vassé |
Paris, Les Invalides | Les Invalides | Dôme des Invalides coupole intérieur | 1677–1706 | Jules Hardouin-Mansart |
Paris, Panthéon | Panthéon | Panthéon Paris coupole intérieur | 1758–90 | Jacques-Germain Soufflot |
Paris, Val-de-Grâce | Val-de-Grâce (church) | Val-de-Grâce coupole Mignard | 1645–67 | François Mansart and Jacques Lemercier; fresco by Pierre Mignard |
Paris, Galeries Lafayette | Galeries Lafayette Haussmann | Galeries Lafayette coupole | 1912 | Ferdinand Chanut; glass by Jacques Gruber | Glass dome
Paris, Bourse de commerce | Bourse de commerce (Paris) | Bourse de commerce Paris coupole | Dome 1806–12; rebuilt 1889 | Dome by François-Joseph Bélanger | Glass and iron dome
Paris, Sacré-Cœur | Sacré-Cœur, Paris | Sacré-Cœur Montmartre coupole intérieur | 1875–1914 | Paul Abadie |
Paris, Petit Palais | Petit Palais | Petit Palais coupole | 1900 | Charles Girault |
Marseille, cathedral | Marseille Cathedral | Cathédrale de la Major coupole intérieur | 1852–96 | Léon Vaudoyer |
Marseille, Vieille Charité | Vieille Charité | Vieille Charité chapelle coupole | 1671–1749 | Pierre Puget | Oval dome
Périgueux, Saint-Front | Périgueux Cathedral | Cathédrale Saint-Front coupole intérieur | 12th century; rebuilt 1852–95 | Rebuilt under Paul Abadie |
Córdoba, Mezquita | Mosque–Cathedral of Córdoba | Mezquita Córdoba cúpula mihrab maqsura | 961–965 | Built for the caliph al-Hakam II |
Granada, Alhambra, Hall of the Two Sisters | Court of the Lions | Sala de Dos Hermanas cúpula mocárabes | 1362–91 | Built for Muhammad V | Muqarnas dome
Granada, Alhambra, Hall of the Abencerrajes | Court of the Lions | Sala de los Abencerrajes cúpula | 1362–91 | Built for Muhammad V | Star-shaped muqarnas dome
Granada, cathedral | Granada Cathedral | Catedral de Granada capilla mayor cúpula | 1523–63 | Diego de Siloé |
Seville, Alcázar, Hall of Ambassadors | Alcázar of Seville | Salón de Embajadores Alcázar Sevilla cúpula | Dome 1427 | Dome by Diego Ruiz | Gilded wooden dome
Seville, San Luis de los Franceses | Church of Saint Louis of France | San Luis de los Franceses cúpula | 1699–1731 | Leonardo de Figueroa |
El Escorial | El Escorial | Basílica El Escorial cúpula interior | 1563–84 | Juan Bautista de Toledo and Juan de Herrera |
Madrid, San Francisco el Grande | San Francisco el Grande Basilica | San Francisco el Grande Madrid cúpula | 1761–84 | Francisco Cabezas, completed by Francesco Sabatini |
Madrid, San Antonio de la Florida | Royal Chapel of St. Anthony of La Florida | San Antonio de la Florida cúpula Goya | 1792–98 | Filippo Fontana; fresco by Francisco Goya |
Zaragoza, El Pilar | Cathedral-Basilica of Our Lady of the Pillar | Basílica del Pilar cúpula Goya Regina Martyrum | 1681–1872 | |
Burgos, cathedral | Burgos Cathedral | Catedral de Burgos cimborrio | Lantern 1539–68 | Juan de Vallejo | Star vault
Burgos, Chapel of the Constable | Burgos Cathedral | Capilla del Condestable Burgos bóveda | 1482–94 | Simón de Colonia | Star vault
Valencia, Basilica of the Forsaken | Basilica of Our Lady of the Forsaken | Basílica de los Desamparados cúpula Palomino | 1652–67; fresco 1701 | Fresco by Antonio Palomino | Oval dome
Salamanca, New Cathedral | New Cathedral of Salamanca | Catedral Nueva Salamanca cúpula | Dome 18th century | |
Lisbon, Estrela Basilica | Estrela Basilica | Basílica da Estrela cúpula interior | 1779–90 | Mateus Vicente de Oliveira and Reinaldo Manuel |
Mafra | Palace of Mafra | Basílica de Mafra cúpula | 1717–30 | João Frederico Ludovice |
Oxford, Radcliffe Camera | Radcliffe Camera | Radcliffe Camera dome interior | 1737–49 | James Gibbs |
London, British Museum Reading Room | British Museum Reading Room | British Museum Reading Room dome | 1854–57 | Sydney Smirke |
London, St Stephen Walbrook | St Stephen Walbrook | St Stephen Walbrook dome | 1672–79 | Sir Christopher Wren |
London, Brompton Oratory | Brompton Oratory | Brompton Oratory dome interior | 1880–84; dome 1895–96 | Herbert Gribble |
London, Leadenhall Market | Leadenhall Market | Leadenhall Market dome roof | 1881 | Sir Horace Jones |
Brighton, Royal Pavilion | Royal Pavilion | Royal Pavilion Brighton music room ceiling dome | 1815–22 | John Nash |
York, Minster chapter house | York Minster | York Minster chapter house ceiling vault | 1260–86 | | Eight-sided vault
Wells, chapter house | Wells Cathedral | Wells Cathedral chapter house vault ceiling | 1286–1306 | | Eight-sided vault
Lincoln, chapter house | Lincoln Cathedral | Lincoln Cathedral chapter house vault | 1220–35 | | Ten-sided vault
Salisbury, chapter house | Salisbury Cathedral | Salisbury Cathedral chapter house vault ceiling | 1263–84 | | Eight-sided vault
London, Westminster Abbey chapter house | Westminster Abbey | Westminster Abbey chapter house vault ceiling | 1246–55 | | Eight-sided vault
Ely, octagon | Ely Cathedral | Ely Cathedral octagon lantern | 1322–42 | Alan of Walsingham and William Hurley | Eight-sided lantern
Castle Howard | Castle Howard | Castle Howard great hall dome | 1699–1712; dome rebuilt after the fire of 1940 | Sir John Vanbrugh |
London, Chiswick House | Chiswick House | Chiswick House dome saloon ceiling | 1726–29 | Lord Burlington |
Edinburgh, McEwan Hall | McEwan Hall | McEwan Hall dome interior | 1888–97 | Sir Robert Rowand Anderson |
Edinburgh, General Register House | General Register House | General Register House dome rotunda | 1774–88 | Robert Adam |
Liverpool, Picton Reading Room | Picton Reading Room and Hornby Library | Picton Reading Room dome | 1875–79 | Cornelius Sherlock |
Liverpool, Port of Liverpool Building | Port of Liverpool Building | Port of Liverpool Building dome interior | 1904–07 | Sir Arnold Thornely and F. B. Hobbs |
Buxton, Devonshire Dome | Devonshire Dome | Devonshire Dome Buxton interior | Building 1780–89; dome 1881 | John Carr; dome by Robert Rippon Duke |
Belfast, City Hall | Belfast City Hall | Belfast City Hall dome interior | 1898–1906 | Sir Alfred Brumwell Thomas |
Dublin, City Hall | City Hall, Dublin | City Hall Dublin rotunda dome | 1769–79 | Thomas Cooley |
Dublin, Four Courts | Four Courts | Four Courts Dublin dome interior | 1786–1802; rebuilt 1924–31 | James Gandon |
Dublin, National Museum | National Museum of Ireland – Archaeology | National Museum of Ireland rotunda dome | 1885–90 | Thomas Newenham Deane and Thomas Manly Deane |
Berlin, cathedral | Berlin Cathedral | Berliner Dom Kuppel innen | 1894–1905 | Julius Raschdorff |
Berlin, Bode Museum | Bode Museum | Bode-Museum Kuppel innen | 1897–1904 | Ernst von Ihne |
Potsdam, St Nicholas | St. Nicholas Church, Potsdam | Nikolaikirche Potsdam Kuppel innen | 1830–50 | Karl Friedrich Schinkel; dome by Ludwig Persius and Friedrich August Stüler |
Aachen, Palatine Chapel | Palatine Chapel, Aachen | Aachener Dom Oktogon Kuppel Mosaik | About 796–805; mosaic 1880–81 | Odo of Metz | Eight-sided vault
Cologne, St Gereon | St. Gereon's Basilica | St. Gereon Köln Dekagon Kuppel | Decagon 1219–27 | | Ten-sided dome
Munich, Theatine Church | Theatine Church, Munich | Theatinerkirche München Kuppel innen | 1663–90 | Agostino Barelli and Enrico Zuccalli |
Munich, Palace of Justice | Justizpalast (Munich) | Justizpalast München Kuppel Lichthof | 1890–97 | Friedrich von Thiersch | Glass dome
Ettal Abbey | Ettal Abbey | Kloster Ettal Kuppel Fresko | 1710–52 | Enrico Zuccalli and Joseph Schmuzer; fresco by Johann Jakob Zeiller |
Weingarten Abbey | Weingarten Abbey | Basilika Weingarten Kuppel | 1715–24 | |
Wies | Wieskirche | Wieskirche Deckenfresko | 1745–54 | Dominikus Zimmermann | Oval vault
St. Blasien | St. Blaise Abbey, Black Forest | Dom St. Blasien Kuppel innen | 1768–83 | Pierre Michel d'Ixnard |
Kelheim, Befreiungshalle | Befreiungshalle | Befreiungshalle Kelheim Kuppel innen | 1842–63 | Friedrich von Gärtner, completed by Leo von Klenze |
Fulda, cathedral | Fulda Cathedral | Fuldaer Dom Kuppel innen | 1704–12 | Johann Dientzenhofer |
Leipzig, Monument to the Battle of the Nations | Monument to the Battle of the Nations | Völkerschlachtdenkmal Kuppel innen Reiter | 1898–1913 | Bruno Schmitz |
Darmstadt, St Ludwig | St. Ludwig, Darmstadt | St. Ludwig Darmstadt Kuppel innen | 1822–27 | Georg Moller |
Salzburg, cathedral | Salzburg Cathedral | Salzburger Dom Kuppel innen | 1614–28 | Santino Solari |
Salzburg, Kollegienkirche | Kollegienkirche, Salzburg | Kollegienkirche Salzburg Kuppel | 1694–1707 | Johann Bernhard Fischer von Erlach |
Vienna, Hofburg, St Michael's Wing | Hofburg | Michaelerkuppel Hofburg innen | 1889–93 | After a design by Joseph Emanuel Fischer von Erlach |
Vienna, National Library | Austrian National Library | Prunksaal Nationalbibliothek Kuppel Fresko | 1723–26 | Johann Bernhard Fischer von Erlach and his son; fresco by Daniel Gran | Oval dome
Vienna, Natural History Museum | Natural History Museum, Vienna | Naturhistorisches Museum Wien Kuppel innen | 1871–89 | Gottfried Semper and Karl von Hasenauer |
Graz, mausoleum | Mausoleum of Emperor Ferdinand II | Mausoleum Graz Kuppel innen | 1614–38 | Giovanni Pietro de Pomis | The dome over St Catherine's Church, which the mausoleum adjoins
Bern, Federal Palace | Federal Palace of Switzerland | Bundeshaus Bern Kuppel innen | 1894–1902 | Hans Wilhelm Auer |
St. Gallen, cathedral | Abbey of Saint Gall | Kathedrale St. Gallen Rotunde Kuppel Fresko | 1755–66 | Peter Thumb and Johann Michael Beer |
Einsiedeln Abbey | Einsiedeln Abbey | Kloster Einsiedeln Kuppel | 1719–35 | Kaspar Moosbrugger |
Prague, St Francis | Church of St. Francis of Assisi (Prague) | Kostel svatého Františka z Assisi Praha kupole | 1679–88 | Jean Baptiste Mathey |
Kroměříž, Flower Garden rotunda | Kroměříž | Květná zahrada Kroměříž rotunda kupole | 1665–75 | Filiberto Lucchese and Giovanni Pietro Tencalla |
Wrocław, Centennial Hall | Centennial Hall (Wrocław) | Hala Stulecia Wrocław kopuła wnętrze | 1911–13 | Max Berg | Concrete ribbed dome
Kraków, Sigismund's Chapel | Sigismund's Chapel | Kaplica Zygmuntowska kopuła | 1519–33 | Bartolommeo Berrecci |
Vilnius, Sts Peter and Paul | Church of St. Peter and St. Paul, Vilnius | Šv. Petro ir Povilo bažnyčia kupolas | 1668–1701 | |
Helsinki, cathedral | Helsinki Cathedral | Helsinki Cathedral dome interior | 1830–52 | Carl Ludvig Engel |
Helsinki, National Library | National Library of Finland | National Library of Finland rotunda dome | 1836–45; rotunda 1902–06 | Carl Ludvig Engel; rotunda by Gustaf Nyström |
Stockholm, Skeppsholm Church | Skeppsholmen Church | Skeppsholmskyrkan kupol | 1824–42 | Fredrik Blom |
Stockholm, Gustaf Vasa Church | Gustaf Vasa Church | Gustaf Vasa kyrka kupol | 1901–06 | Agi Lindegren |
Copenhagen, Marble Church | Frederik's Church | Marmorkirken kuppel | 1749–1894 | Nicolai Eigtved, completed by Ferdinand Meldahl |
Copenhagen, Christiansborg Palace Chapel | Christiansborg Palace Chapel | Christiansborg Slotskirke kuppel | 1813–26 | Christian Frederik Hansen |
Brussels, Palace of Justice | Palace of Justice, Brussels | Palais de Justice Bruxelles coupole intérieur | 1866–83 | Joseph Poelaert |
Scherpenheuvel | Basilica of Our Lady of Scherpenheuvel | Basiliek Scherpenheuvel koepel | 1609–27 | Wenceslas Cobergher |
Antwerp, Central Station | Antwerpen-Centraal railway station | Antwerpen Centraal koepel | 1895–1905 | Louis Delacenserie |
Haarlem, Cathedral of St Bavo | Cathedral of St Bavo, Haarlem | Koepelkathedraal Haarlem koepel | 1895–1930 | Joseph Cuypers |
Breda, dome prison | Koepelgevangenis (Breda) | Koepelgevangenis Breda koepel interieur | 1882–86 | Johan Frederik Metzelaar | Iron dome over a round prison
St Petersburg, Kazan Cathedral | Kazan Cathedral, Saint Petersburg | Казанский собор купол интерьер | 1801–11 | Andrey Voronikhin |
St Petersburg, Church of the Savior on Blood | Church of the Savior on Blood | Спас на Крови купол мозаика | 1883–1907 | Alfred Parland |
Kronstadt, Naval Cathedral | Kronstadt Naval Cathedral | Морской собор Кронштадт купол интерьер | 1903–13 | Vasily Kosyakov |
Moscow, St Basil's | Saint Basil's Cathedral | Saint Basil's Cathedral interior tent dome spiral | 1555–61 | Traditionally Barma and Postnik Yakovlev | Tent roof with a spiral in its crown
Kyiv, St Sophia | Saint Sophia Cathedral, Kyiv | Софійський собор Київ купол Пантократор | 11th century | Built for Yaroslav the Wise |
Kyiv, St Andrew's | St Andrew's Church, Kyiv | Андріївська церква Київ купол інтер'єр | 1747–54 | Bartolomeo Rastrelli |
Kyiv, St Volodymyr's | St Volodymyr's Cathedral | Володимирський собор Київ купол | 1862–82 | |
Lviv, Boim Chapel | Boim Chapel | Каплиця Боїмів купол | 1609–15 | |
Bucharest, Romanian Athenaeum | Romanian Athenaeum | Ateneul Român cupola interior | 1886–88 | Albert Galleron |
Bucharest, CEC Palace | CEC Palace | Palatul CEC cupola interior | 1897–1900 | Paul Gottereau | Glass dome
Split, cathedral | Cathedral of Saint Domnius | Split cathedral Diocletian mausoleum dome interior | About 305 | Built as the tomb of the emperor Diocletian |
Budapest, Museum of Applied Arts | Museum of Applied Arts (Budapest) | Iparművészeti Múzeum kupola | 1893–96 | Ödön Lechner and Gyula Pártos | Glass dome
Budapest, Rudas Baths | Rudas Baths | Rudas fürdő kupola török | About 1566–72 | Built for Sokollu Mustafa Pasha |
Sarajevo, Gazi Husrev-beg Mosque | Gazi Husrev-beg Mosque | Gazi Husrev-begova džamija kupola unutrašnjost | 1530–31 | Acem Esir Ali |
Mostar, Koski Mehmed Pasha Mosque | Koski Mehmed Pasha Mosque | Koski Mehmed-pašina džamija kupola | 1617–19 | |
Tetovo, Painted Mosque | Šarena Džamija | Šarena Džamija Tetovo interior dome | 1438; rebuilt 1833 | Rebuilt for Abdurrahman Pasha | Painted dome
Prizren, Sinan Pasha Mosque | Sinan Pasha Mosque (Prizren) | Sinan Pasha Mosque Prizren interior dome | 1615 | Built for Sofi Sinan Pasha |
Tirana, Et'hem Bey Mosque | Et'hem Bey Mosque | Et'hem Bey Mosque interior dome | About 1791–1821 | Begun by Molla Bey, completed by his son Haxhi Ethem Bey | Painted dome
Thessaloniki, Rotunda | Rotunda (Thessaloniki) | Rotunda Thessaloniki dome mosaic interior | About 306; mosaics 4th–6th centuries | Built for the emperor Galerius |
Thessaloniki, Hagia Sophia | Hagia Sophia, Thessaloniki | Hagia Sophia Thessaloniki dome Ascension mosaic | 7th–8th centuries; dome mosaic 9th century | |
Daphni Monastery | Daphni Monastery | Daphni Monastery dome Pantocrator mosaic | About 1080 | |
Hosios Loukas | Hosios Loukas | Hosios Loukas katholikon dome | 11th century | |
Mycenae, Treasury of Atreus | Treasury of Atreus | Treasury of Atreus interior dome tholos | About 1300–1250 BC | | Corbelled stone dome
Kazanlak, Thracian tomb | Thracian Tomb of Kazanlak | Kazanlak tomb dome fresco | 4th–3rd century BC | | Painted corbelled dome
Sofia, Rotunda of St George | Church of Saint George, Sofia | Rotunda St George Sofia dome fresco | 4th century; frescoes 10th–14th centuries | |
Etchmiadzin Cathedral | Etchmiadzin Cathedral | Etchmiadzin Cathedral dome interior fresco | 483; dome frescoes 18th century | |
Geghard | Geghard | Geghard gavit dome stalactite | 1215–25 | | Stalactite vault with an opening at the crown
Istanbul, Hagia Sophia | Hagia Sophia | Hagia Sophia dome interior from below | 532–537; dome rebuilt 558–562 | Anthemius of Tralles and Isidore of Miletus; the dome by Isidore the Younger |
Istanbul, Süleymaniye | Süleymaniye Mosque | Süleymaniye Mosque dome interior | 1550–57 | Mimar Sinan, for Sultan Suleiman the Magnificent |
Istanbul, Blue Mosque | Blue Mosque, Istanbul | Sultan Ahmed Mosque dome interior | 1609–16 | Sedefkâr Mehmed Ağa, for Sultan Ahmed I |
Istanbul, Şehzade | Şehzade Mosque | Şehzade Mosque dome interior | 1543–48 | Mimar Sinan |
Istanbul, Rüstem Pasha | Rüstem Pasha Mosque | Rüstem Pasha Mosque dome interior | 1561–63 | Mimar Sinan |
Istanbul, Mihrimah Sultan | Mihrimah Sultan Mosque (Edirnekapı) | Mihrimah Sultan Mosque Edirnekapı dome interior | 1562–65 | Mimar Sinan |
Istanbul, Sokollu Mehmed Pasha | Sokollu Mehmed Pasha Mosque (Kadırga) | Sokollu Mehmed Pasha Mosque Kadırga dome | 1568–72 | Mimar Sinan |
Istanbul, New Mosque | New Mosque, Istanbul | Yeni Cami Istanbul dome interior | 1597–1665 | Davut Ağa, Dalgıç Ahmed Çavuş and Mustafa Ağa |
Istanbul, Nuruosmaniye | Nuruosmaniye Mosque | Nuruosmaniye Mosque dome interior | 1748–55 | Simeon Kalfa |
Istanbul, Ortaköy | Ortaköy Mosque | Ortaköy Mosque dome interior | 1854–56 | Garabet and Nigoğayos Balyan |
Istanbul, Dolmabahçe Palace | Dolmabahçe Palace | Dolmabahçe Palace ceremonial hall dome | 1843–56 | Garabet and Nigoğayos Balyan |
Istanbul, Chora | Chora Church | Chora Church dome mosaic Kariye | Mosaics and frescoes 1315–21 | Rebuilt for Theodore Metochites |
Istanbul, Pammakaristos | Pammakaristos Church | Pammakaristos Fethiye dome Pantocrator mosaic | About 1310 | |
Istanbul, Bayezid II | Bayezid II Mosque, Istanbul | Bayezid II Mosque Istanbul dome interior | 1501–06 | |
Istanbul, Fatih | Fatih Mosque, Istanbul | Fatih Mosque dome interior | Rebuilt 1767–71 | Rebuilt by Mehmed Tahir Ağa |
Istanbul, Kılıç Ali Pasha | Kılıç Ali Pasha Complex | Kılıç Ali Pasha Mosque dome interior | 1578–80 | Mimar Sinan |
Istanbul, Çemberlitaş Bath | Çemberlitaş Hamamı | Çemberlitaş Hamamı dome | 1584 | Mimar Sinan | Bath dome pierced with small lights
Bursa, Green Mosque | Green Mosque, Bursa | Yeşil Cami Bursa dome interior | 1412–24 | Hacı İvaz Pasha |
Bursa, Grand Mosque | Grand Mosque of Bursa | Bursa Ulu Cami dome interior | 1396–99 | Ali Neccar | One of twenty domes
Konya, Karatay Madrasa | Karatay Madrasa | Karatay Medresesi kubbe | 1251–52 | Built for Celaleddin Karatay | Tiled dome with an opening at the crown
Konya, İnce Minareli Madrasa | Ince Minaret Medrese | İnce Minareli Medrese kubbe | About 1265 | Built for Sahip Ata Fahreddin Ali |
Divriği, Great Mosque | Great Mosque and Hospital of Divriği | Divriği Ulu Camii kubbe tonoz | 1228–29 | Hürrem Shah of Ahlat | Carved stone vault
Jerusalem, Dome of the Rock | Dome of the Rock | Dome of the Rock interior dome | 688–692; dome 1022 | Built for the caliph Abd al-Malik |
Jerusalem, Church of the Holy Sepulchre | Church of the Holy Sepulchre | Church of the Holy Sepulchre rotunda dome | Rotunda 4th century; dome rebuilt 1868, restored 1997 | |
Damascus, Khan As'ad Pasha | Khan As'ad Pasha | Khan As'ad Pasha dome interior | 1751–52 | Built for As'ad Pasha al-Azm | One of nine domes
Cairo, Sultan Hassan | Mosque-Madrasa of Sultan Hasan | Sultan Hassan mosque mausoleum dome interior | 1356–63 | |
Cairo, Qalawun complex | Qalawun complex | Qalawun mausoleum dome interior Cairo | 1284–85; dome rebuilt 1903 | Built for Sultan al-Mansur Qalawun |
Cairo, Mosque of Muhammad Ali | Mosque of Muhammad Ali | Muhammad Ali Mosque Cairo dome interior | 1830–48 | Yusuf Bushnak |
Cairo, Al-Rifa'i Mosque | Al-Rifa'i Mosque | Al-Rifa'i Mosque Cairo dome interior | 1869–1912 | Hussein Fahmy Pasha, completed by Max Herz |
Cairo, Qaitbay | Mosque of Qaitbay | Qaitbay mausoleum dome interior | 1472–74 | Built for Sultan al-Ashraf Qaitbay |
Cairo, Imam al-Shafi'i | Mausoleum of Imam al-Shafi'i | Imam al-Shafi'i mausoleum dome interior | 1211 | Built for the Ayyubid sultan al-Kamil | Wooden dome
Kairouan, Great Mosque | Great Mosque of Kairouan | Great Mosque of Kairouan mihrab dome interior | 836–862 | |
Marrakech, Almoravid Koubba | Almoravid Qubba | Koubba Almoravide Marrakech coupole intérieur | About 1117–25 | Built for Ali ibn Yusuf |
Marrakech, Saadian Tombs | Saadian Tombs | Tombeaux Saadiens coupole cèdre | Late 16th century | Built for Ahmad al-Mansur | Cedar dome
Tlemcen, Great Mosque | Great Mosque of Tlemcen | Grande Mosquée Tlemcen coupole mihrab | Dome 1136 | Built for Ali ibn Yusuf | Pierced ribbed dome
Isfahan, Shah Mosque | Shah Mosque (Isfahan) | Shah Mosque Isfahan dome interior | 1611–29 | Ali Akbar Isfahani, for Shah Abbas I |
Isfahan, Friday Mosque, north dome | Jameh Mosque of Isfahan | Jameh Mosque Isfahan Taj al-Mulk dome interior | 1088–89 | Built for Taj al-Mulk |
Isfahan, Friday Mosque, south dome | Jameh Mosque of Isfahan | Jameh Mosque Isfahan Nizam al-Mulk dome interior | 1086–87 | Built for Nizam al-Mulk |
Isfahan, Hasht Behesht | Hasht Behesht | Hasht Behesht ceiling muqarnas | 1669 | Built for Shah Suleiman I |
Isfahan, Vank Cathedral | Vank Cathedral | Vank Cathedral dome interior | 1655–64 | | Painted dome
Isfahan, Chahar Bagh School | Chaharbagh School | Madrasa Chahar Bagh Isfahan dome interior | 1704–14 | |
Shiraz, Shah Cheragh | Shah Cheragh | Shah Cheragh dome mirror interior | Shrine 14th century; mirror work 19th century | | Mirror-work dome
Shiraz, Tomb of Hafez | Tomb of Hafez | Tomb of Hafez dome ceiling | Pavilion 1935 | André Godard | Tiled dome over an open pavilion
Kashan, Sultan Amir Ahmad Bathhouse | Sultan Amir Ahmad Bathhouse | Sultan Amir Ahmad Bathhouse dome ceiling | 16th century; rebuilt in the Qajar era | |
Kashan, Agha Bozorg Mosque | Agha Bozorg Mosque | Agha Bozorg Mosque dome interior | Late 18th to mid 19th century | Ustad Haj Sa'ban-ali |
Kashan, Borujerdi House | Borujerdi House | Borujerdi House dome ceiling | 1857 | Ustad Ali Maryam |
Kashan, Timcheh Amin od-Dowleh | Bazaar of Kashan | Timcheh Amin od-Dowleh dome | 1863–68 | Ustad Ali Maryam |
Yazd, Friday Mosque | Jameh Mosque of Yazd | Jameh Mosque Yazd dome interior | 1324–65 | |
Mahan, Shah Nematollah Vali Shrine | Shah Nematollah Vali Shrine | Shah Nematollah Vali Shrine dome interior | 1436; enlarged in the Safavid and Qajar eras | |
Soltaniyeh | Dome of Soltaniyeh | Dome of Soltaniyeh interior | 1302–12 | Built for the Ilkhan Öljaitü |
Tabriz, Blue Mosque | Blue Mosque, Tabriz | Blue Mosque Tabriz dome interior | 1465 | Built for Jahan Shah |
Ardabil, Sheikh Safi shrine | Sheikh Safi al-Din Khānegāh and Shrine Ensemble | Sheikh Safi Ardabil Chini Khaneh dome | 16th–17th centuries | |
Natanz, shrine of Abd al-Samad | Jameh Mosque of Natanz | Natanz Abd al-Samad muqarnas dome | 1307 | | Muqarnas dome
Samarkand, Gur-e-Amir | Gur-e-Amir | Gur-e-Amir dome interior | 1403–04 | Built for Timur |
Samarkand, Tilya-Kori | Registan | Tilya-Kori Madrasa dome interior gold | 1646–60 | Built for Yalangtush Bahadur | A flat ceiling painted to look like a dome
Samarkand, Bibi-Khanym | Bibi-Khanym Mosque | Bibi-Khanym Mosque dome interior | 1399–1404 | Built for Timur |
Samarkand, Shah-i-Zinda | Shah-i-Zinda | Shah-i-Zinda mausoleum dome interior | 14th–15th centuries | |
Bukhara, Samanid Mausoleum | Samanid Mausoleum | Samanid Mausoleum interior dome | About 892–943 | |
Bukhara, Kalan Mosque | Kalan Mosque | Kalon Mosque Bukhara dome interior | 1514 | |
Bukhara, Abdulaziz Khan Madrasa | Abdulaziz Khan Madrasah | Abdulaziz Khan Madrasa Bukhara ceiling muqarnas | 1652 | |
Khiva, Pahlavan Mahmud Mausoleum | Pahlavon Mahmud Mausoleum | Pahlavan Mahmud Mausoleum Khiva dome interior | 1810–35 | | Tiled dome
Shahrisabz, Kok Gumbaz | Kuk Gumbaz Mosque (Shahrisabz) | Kok Gumbaz Shahrisabz dome interior | 1435 | Built for Ulugh Beg |
Turkistan, Mausoleum of Khoja Ahmed Yasawi | Mausoleum of Khoja Ahmed Yasawi | Mausoleum of Khoja Ahmed Yasawi dome interior | 1389–1405 | Built for Timur |
Merv, Mausoleum of Sultan Sanjar | Tomb of Ahmad Sanjar | Sultan Sanjar mausoleum Merv dome interior | 1157 | Muhammad ibn Aziz of Sarakhs |
Agra, Taj Mahal | Taj Mahal | Taj Mahal interior dome ceiling | 1632–53 | Ustad Ahmad Lahauri, for Shah Jahan |
Agra, Tomb of Itimad-ud-Daulah | Tomb of I'timād-ud-Daulah | Itimad-ud-Daulah tomb ceiling interior | 1622–28 | Built for Nur Jahan |
Agra, Akbar's Tomb | Akbar's tomb | Akbar's tomb Sikandra ceiling dome painted | 1605–13 | |
Delhi, Humayun's Tomb | Humayun's Tomb | Humayun's Tomb dome interior | 1565–72 | Mirak Mirza Ghiyas |
Delhi, Safdarjung's Tomb | Tomb of Safdar Jang | Safdarjung Tomb ceiling dome interior | 1754 | |
Delhi, Alai Darwaza | Alai Darwaza | Alai Darwaza dome interior | 1311 | Built for Alauddin Khalji |
Delhi, Jamali Kamali | Jamali Kamali Mosque and Tomb | Jamali Kamali tomb ceiling | 1528–36 | | Painted ceiling
Bijapur, Gol Gumbaz | Gol Gumbaz | Gol Gumbaz dome interior | 1626–56 | Yaqut of Dabul |
Mount Abu, Luna Vasahi | Dilwara Temples | Luna Vasahi Dilwara dome ceiling | 1230 | Built for Vastupala and Tejapala | Carved marble dome
Mount Abu, Vimal Vasahi | Dilwara Temples | Vimal Vasahi Dilwara dome ceiling | 1031 | Built for Vimal Shah | Carved marble dome
Ranakpur | Ranakpur Jain temple | Ranakpur Jain temple dome ceiling | 1437–58 | Depaka, for Dharna Shah | Carved marble dome
Kolkata, Victoria Memorial | Victoria Memorial, Kolkata | Victoria Memorial Kolkata dome interior | 1906–21 | William Emerson |
Mumbai, Chhatrapati Shivaji Terminus | Chhatrapati Shivaji Terminus | Chhatrapati Shivaji Terminus dome interior | 1878–88 | Frederick William Stevens |
Mumbai, General Post Office | General Post Office, Mumbai | Mumbai GPO dome interior | 1904–13 | John Begg |
Mumbai, Prince of Wales Museum | Chhatrapati Shivaji Maharaj Vastu Sangrahalaya | Prince of Wales Museum Mumbai dome interior | 1905–15 | George Wittet |
Mumbai, Taj Mahal Palace | Taj Mahal Palace Hotel | Taj Mahal Palace Hotel dome staircase interior | 1903 | |
Mysore Palace | Mysore Palace | Mysore Palace Kalyana Mantapa stained glass ceiling | 1897–1912 | Henry Irwin | Eight-sided stained glass ceiling
Lahore, Wazir Khan Mosque | Wazir Khan Mosque | Wazir Khan Mosque dome interior fresco | 1634–41 | Built for Wazir Khan |
Lahore, Badshahi Mosque | Badshahi Mosque | Badshahi Mosque dome interior | 1671–73 | Built for Aurangzeb |
Thatta, Shah Jahan Mosque | Shah Jahan Mosque, Thatta | Shah Jahan Mosque Thatta dome interior tile | 1644–47 | | Tile mosaic dome
Multan, Shah Rukn-e-Alam | Tomb of Shah Rukn-e-Alam | Shah Rukn-e-Alam tomb dome interior | 1320–24 | |
Mandu, Hoshang Shah's Tomb | Hoshang Shah's Tomb | Hoshang Shah Tomb Mandu dome interior | About 1440 | |
Ahmedabad, Friday Mosque | Jama Mosque, Ahmedabad | Jama Masjid Ahmedabad dome interior | 1424 | Built for Ahmad Shah I | Corbelled dome
Champaner, Friday Mosque | Jama Mosque, Champaner | Jami Masjid Champaner dome ceiling | About 1508–13 | Built for Mahmud Begada |
Sasaram, Tomb of Sher Shah Suri | Tomb of Sher Shah Suri | Sher Shah Suri tomb dome interior | 1540–45 | Aliwal Khan |
Beijing, Temple of Heaven, Hall of Prayer | Temple of Heaven | Hall of Prayer for Good Harvests interior ceiling | 1420; rebuilt 1890–96 | | A round timber ceiling, not a masonry dome
Beijing, Imperial Vault of Heaven | Temple of Heaven | Imperial Vault of Heaven interior ceiling | 1530; rebuilt 1752 | | A round timber ceiling, not a masonry dome
Shanghai, HSBC Building | HSBC Building, the Bund | HSBC Building Shanghai dome mosaic | 1921–23 | Palmer and Turner | Eight-sided mosaic dome
Tokyo Station | Tokyo Station | Tokyo Station Marunouchi dome interior | 1914; restored 2012 | Tatsuno Kingo |
Tokyo, Hyokeikan | Hyōkeikan | Hyokeikan dome interior | 1909 | Katayama Tōkuma |
Singapore, National Museum | National Museum of Singapore | National Museum of Singapore rotunda dome | 1887 | Henry McCallum |
Jakarta, Immanuel Church | Immanuel Church, Jakarta | Gereja Immanuel Jakarta dome interior | 1834–39 | J. H. Horst |
Washington, Capitol | United States Capitol rotunda | United States Capitol rotunda dome Apotheosis | Dome 1855–66 | Thomas U. Walter; fresco by Constantino Brumidi |
Washington, Library of Congress | Thomas Jefferson Building | Library of Congress reading room dome | 1890–97 | John L. Smithmeyer and Paul J. Pelz |
Washington, Natural History Museum | National Museum of Natural History | National Museum of Natural History rotunda dome | 1904–11 | Hornblower and Marshall |
Washington, St Matthew's | Cathedral of St. Matthew the Apostle (Washington, D.C.) | Cathedral of St. Matthew Washington dome interior | 1893–1913 | Christopher Grant LaFarge |
Charlottesville, Rotunda | The Rotunda (University of Virginia) | University of Virginia Rotunda dome room | 1822–26; rebuilt after the fire of 1895 | Thomas Jefferson |
Baltimore, Basilica | Basilica of the National Shrine of the Assumption of the Blessed Virgin Mary | Baltimore Basilica dome interior | 1806–21 | Benjamin Henry Latrobe |
Annapolis, State House | Maryland State House | Maryland State House dome interior | Dome 1785–94 | Joseph Clark | Wooden dome
Boston, Quincy Market | Quincy Market | Quincy Market rotunda dome | 1824–26 | Alexander Parris |
Cambridge, MIT Great Dome | Great Dome (MIT) | MIT Great Dome interior Barker Library | 1916 | William Welles Bosworth |
New York, Low Memorial Library | Low Memorial Library | Low Memorial Library rotunda dome | 1895–97 | Charles Follen McKim |
New York, Gould Memorial Library | Gould Memorial Library | Gould Memorial Library dome interior | 1899 | Stanford White |
New York, City Hall | New York City Hall | New York City Hall rotunda dome | 1803–12 | Joseph-François Mangin and John McComb Jr. |
New York, Federal Hall | Federal Hall | Federal Hall rotunda dome | 1834–42 | Ithiel Town and Alexander Jackson Davis |
New York, Grant's Tomb | Grant's Tomb | Grant's Tomb dome interior | 1891–97 | John H. Duncan |
New York, Custom House | Alexander Hamilton U.S. Custom House | Alexander Hamilton Custom House rotunda dome | 1902–07 | Cass Gilbert |
New York, Williamsburgh Savings Bank | Williamsburgh Savings Bank Building (175 Broadway) | Williamsburgh Savings Bank 175 Broadway dome interior | 1870–75 | George B. Post |
Philadelphia, cathedral | Cathedral Basilica of Saints Peter and Paul, Philadelphia | Cathedral Basilica of Saints Peter and Paul Philadelphia dome | 1846–64 | Napoleon LeBrun and John Notman |
Harrisburg, State Capitol | Pennsylvania State Capitol | Pennsylvania State Capitol rotunda dome | 1902–06 | Joseph Miller Huston |
Austin, State Capitol | Texas State Capitol | Texas State Capitol rotunda dome | 1882–88 | Elijah E. Myers |
Madison, State Capitol | Wisconsin State Capitol | Wisconsin State Capitol rotunda dome | 1906–17 | George B. Post |
Saint Paul, State Capitol | Minnesota State Capitol | Minnesota State Capitol rotunda dome | 1896–1905 | Cass Gilbert |
Des Moines, State Capitol | Iowa State Capitol | Iowa State Capitol rotunda dome | 1871–86 | John C. Cochrane and Alfred H. Piquenard |
Springfield, State Capitol | Illinois State Capitol | Illinois State Capitol rotunda dome | 1868–88 | John C. Cochrane and Alfred H. Piquenard |
Indianapolis, Statehouse | Indiana Statehouse | Indiana Statehouse rotunda dome | 1878–88 | Edwin May, completed by Adolph Scherrer |
Lansing, State Capitol | Michigan State Capitol | Michigan State Capitol rotunda dome | 1872–78 | Elijah E. Myers |
Denver, State Capitol | Colorado State Capitol | Colorado State Capitol rotunda dome | 1886–1907 | Elijah E. Myers |
Topeka, State Capitol | Kansas State Capitol | Kansas State Capitol rotunda dome | 1866–1903 | |
Jefferson City, State Capitol | Missouri State Capitol | Missouri State Capitol rotunda dome | 1913–17 | Tracy and Swartwout |
Frankfort, State Capitol | Kentucky State Capitol | Kentucky State Capitol rotunda dome | 1905–09 | Frank Mills Andrews |
Jackson, State Capitol | Mississippi State Capitol | Mississippi State Capitol rotunda dome | 1901–03 | Theodore Link |
Little Rock, State Capitol | Arkansas State Capitol | Arkansas State Capitol rotunda dome | 1899–1915 | George R. Mann, completed by Cass Gilbert |
Salt Lake City, State Capitol | Utah State Capitol | Utah State Capitol rotunda dome | 1912–16 | Richard K. A. Kletting |
Boise, State Capitol | Idaho State Capitol | Idaho State Capitol rotunda dome | 1905–20 | John E. Tourtellotte and Charles Hummel |
Helena, State Capitol | Montana State Capitol | Montana State Capitol rotunda dome | 1896–1902 | Charles Emlen Bell and John Hackett Kent |
Cheyenne, State Capitol | Wyoming State Capitol | Wyoming State Capitol rotunda dome | 1886–90 | David W. Gibbs |
Pierre, State Capitol | South Dakota State Capitol | South Dakota State Capitol rotunda dome | 1905–10 | Charles Emlen Bell and Menno S. Detweiler |
Olympia, Legislative Building | Washington State Capitol | Washington State Capitol rotunda dome | 1922–28 | Walter Wilder and Harry White |
Sacramento, State Capitol | California State Capitol | California State Capitol rotunda dome | 1860–74 | |
Atlanta, State Capitol | Georgia State Capitol | Georgia State Capitol rotunda dome | 1884–89 | Edbrooke and Burnham |
Providence, State House | Rhode Island State House | Rhode Island State House rotunda dome | 1895–1904 | McKim, Mead and White |
Hartford, State Capitol | Connecticut State Capitol | Connecticut State Capitol dome interior | 1872–79 | Richard M. Upjohn |
Charleston, State Capitol | West Virginia State Capitol | West Virginia State Capitol rotunda dome | 1924–32 | Cass Gilbert |
Lincoln, State Capitol | Nebraska State Capitol | Nebraska State Capitol rotunda dome mosaic | 1922–32 | Bertram Grosvenor Goodhue |
Columbus, Statehouse | Ohio Statehouse | Ohio Statehouse rotunda dome | 1839–61 | |
Baton Rouge, Old State Capitol | Old Louisiana State Capitol | Old Louisiana State Capitol stained glass dome | 1847–52; rebuilt 1882 | James H. Dakin; rebuilt by William A. Freret | Stained glass dome
Tallahassee, Old Capitol | Florida State Capitol | Florida Old Capitol dome stained glass | Dome 1902 | Frank Pierce Milburn |
Montgomery, State Capitol | Alabama State Capitol | Alabama State Capitol rotunda dome | 1850–51 | |
Columbia, State House | South Carolina State House | South Carolina State House dome interior | 1855–1907 | |
Raleigh, State Capitol | North Carolina State Capitol | North Carolina State Capitol rotunda dome | 1833–40 | Town and Davis, and David Paton |
Richmond, State Capitol | Virginia State Capitol | Virginia State Capitol rotunda dome | 1785–88 | Thomas Jefferson and Charles-Louis Clérisseau |
Trenton, State House | New Jersey State House | New Jersey State House rotunda dome | Dome 1889 | Lewis Broome |
Fort Wayne, Allen County Courthouse | Allen County Courthouse (Indiana) | Allen County Courthouse Fort Wayne rotunda dome | 1897–1902 | Brentwood S. Tolan |
Chicago, Cultural Center | Chicago Cultural Center | Chicago Cultural Center Tiffany dome Preston Bradley Hall | 1893–97 | Shepley, Rutan and Coolidge | Stained glass dome
Milwaukee, Basilica of St Josaphat | Basilica of St. Josaphat | Basilica of St. Josaphat dome interior | 1896–1901 | Erhard Brielmaier |
St. Louis, Cathedral Basilica | Cathedral Basilica of Saint Louis (St. Louis) | Cathedral Basilica of Saint Louis dome mosaic | 1907–14; mosaics completed 1988 | Barnett, Haynes and Barnett |
St. Louis, Old Courthouse | Old Courthouse (St. Louis) | Old Courthouse St. Louis rotunda dome | Dome 1861–64 | William Rumbold |
Cleveland, Cleveland Trust rotunda | Cleveland Trust Company Building | Cleveland Trust rotunda stained glass dome | 1905–08 | George B. Post | Stained glass dome
Pittsburgh, Union Station | Union Station (Pittsburgh) | Pennsylvanian Pittsburgh rotunda dome | 1898–1903 | Daniel Burnham |
San Francisco, City Hall | San Francisco City Hall | San Francisco City Hall rotunda dome interior | 1913–15 | Arthur Brown Jr. |
San Francisco, Emporium dome | Westfield San Francisco Centre | Westfield San Francisco Centre dome Emporium | 1908 | Albert Pissis | Glass dome
San Francisco, Columbarium | San Francisco Columbarium & Funeral Home | San Francisco Columbarium dome interior | 1898 | Bernard J. S. Cahill |
San Francisco, City of Paris rotunda | City of Paris Dry Goods Co. | City of Paris rotunda Neiman Marcus San Francisco stained glass | 1909 | | Stained glass dome
Los Angeles, Central Library | Los Angeles Central Library | Los Angeles Central Library rotunda dome | 1926 | Bertram Grosvenor Goodhue |
Los Angeles, City Hall | Los Angeles City Hall | Los Angeles City Hall rotunda dome | 1928 | John Parkinson, John C. Austin and Albert C. Martin |
West Baden Springs Hotel | West Baden Springs Hotel | West Baden Springs Hotel dome atrium | 1901–02 | Harrison Albright |
Ottawa, Library of Parliament | Library of Parliament | Library of Parliament Ottawa dome interior | 1859–76 | Thomas Fuller and Chilion Jones |
Montreal, Mary Queen of the World | Mary, Queen of the World Cathedral | Cathédrale Marie-Reine-du-Monde coupole intérieur | 1875–94 | Victor Bourgeau |
Montreal, Bank of Montreal | Bank of Montreal Head Office, Montreal | Bank of Montreal head office dome interior | 1845–47; enlarged 1901–05 | John Wells; enlarged by McKim, Mead and White |
Winnipeg, Legislative Building | Manitoba Legislative Building | Manitoba Legislative Building rotunda dome | 1913–20 | Frank Worthington Simon |
Regina, Legislative Building | Saskatchewan Legislative Building | Saskatchewan Legislative Building rotunda dome | 1908–12 | Edward and William Sutherland Maxwell |
Edmonton, Legislature Building | Alberta Legislature Building | Alberta Legislature Building rotunda dome | 1907–13 | Allan Merrick Jeffers and Richard Blakey |
Victoria, Parliament Buildings | British Columbia Parliament Buildings | British Columbia Parliament Buildings rotunda dome | 1893–98 | Francis Rattenbury |
Toronto, Bank of Montreal hall | Hockey Hall of Fame | Hockey Hall of Fame Great Hall stained glass dome | 1885 | Darling and Curry | Stained glass dome
Mexico City, Palace of Fine Arts | Palacio de Bellas Artes | Palacio de Bellas Artes cúpula interior | 1904–34 | Adamo Boari, completed by Federico Mariscal |
Mexico City, Metropolitan Cathedral | Mexico City Metropolitan Cathedral | Catedral Metropolitana México cúpula interior | Dome 1813 | Dome by Manuel Tolsá |
Puebla, Chapel of the Rosary | Chapel of the Rosario, Puebla | Capilla del Rosario Puebla cúpula | 1650–90 | |
Tonantzintla | Church of Santa María Tonantzintla | Santa María Tonantzintla cúpula | 18th century | |
Puebla, cathedral | Puebla Cathedral | Catedral de Puebla cúpula interior | Dome 1649 | Dome by Pedro García Ferrer |
Oaxaca, Santo Domingo | Church of Santo Domingo de Guzmán (Oaxaca) | Santo Domingo Oaxaca cúpula interior | 1575–1608 | |
Guadalajara, Hospicio Cabañas | Hospicio Cabañas | Hospicio Cabañas cúpula Orozco Hombre de Fuego | 1805–10; murals 1936–39 | Manuel Tolsá; murals by José Clemente Orozco |
Havana, El Capitolio | El Capitolio | Capitolio Habana cúpula interior | 1926–29 | Raúl Otero and Eugenio Rayneri Piedra |
Quito, La Compañía | Church of La Compañía, Quito | La Compañía Quito cúpula interior | 1605–1765 | |
Lima, San Francisco | Basilica and Convent of San Francisco, Lima | Convento San Francisco Lima cúpula mudéjar escalera | 1625; since restored | | Carved cedar dome over the stair
Cusco, La Compañía | Church of the Society of Jesus (Cusco) | Compañía de Jesús Cusco cúpula interior | 1651–68 | |
Buenos Aires, Congress | Palace of the Argentine National Congress | Congreso Nacional Argentina cúpula interior | 1898–1906 | Vittorio Meano |
Córdoba (Argentina), cathedral | Cathedral of Córdoba, Argentina | Catedral de Córdoba Argentina cúpula interior | Dome 1758 | |
Rio de Janeiro, Candelária | Candelária Church | Igreja da Candelária cúpula interior | 1775–1898 | |
Melbourne, Royal Exhibition Building | Royal Exhibition Building | Royal Exhibition Building dome interior | 1879–80 | Joseph Reed |
Melbourne, State Library | State Library Victoria | La Trobe Reading Room dome | 1909–13 | Bates, Peebles and Smart | Concrete dome
Melbourne, Supreme Court Library | Supreme Court of Victoria | Supreme Court Library Melbourne dome | 1877–84 | Smith and Johnson |
Melbourne, 333 Collins Street | 333 Collins Street | 333 Collins Street dome banking chamber | 1891 | Lloyd Tayler and Alfred Dunn |
Sydney, Queen Victoria Building | Queen Victoria Building | Queen Victoria Building dome interior | 1893–98 | George McRae |
Newgrange | Newgrange | Newgrange chamber corbelled roof | About 3200 BC | | Corbelled stone roof
Maeshowe | Maeshowe | Maeshowe chamber interior roof | About 2800 BC | | Corbelled stone roof
Nuraghe Santu Antine | Nuraghe Santu Antine | Nuraghe Santu Antine tholos interno | Bronze Age, about 1600 BC | | Corbelled stone dome
Centcelles | Centcelles | Centcelles cúpula mosaic | 4th century | | Roman mosaic dome
"""


def domes():
    out = []
    for line in RAW.strip().splitlines():
        p = [x.strip() for x in line.split("|")]
        assert len(p) == 6, line
        out.append({"place": p[0], "wiki": p[1], "query": p[2] or p[1] + " dome interior", "built": p[3], "by": p[4], "note": p[5]})
    assert len({d["place"] for d in out}) == len(out), "a place is listed twice"
    return out


if __name__ == "__main__":
    print(len(domes()), "domes listed")
