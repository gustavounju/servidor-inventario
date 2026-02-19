
import sqlite3

DB_FILE = "inventario.db"

RAW_DATA = """
Adolfo Adolino\tRios\tarios
Adriana\tPeralta\taperalta
Adriana\tGarcia\tagarcia
Agustina\tFayos\tafayos
Agustina\tHeumuller\taheumuller
alba noemi\trojas\tanrojas
Alberto\tLeguizamon\taleguizamon
Alejandro\tLarrosa Carrizo\talarrosacarrizo
Alicia\tLorente\talorente
Alicia\tPintos\tapintos
Alicia\tAldonate\tAaldonate
Alicia Adriana\tMartinez\tamartinez
Amara Nahir\tJayat\tajayat
America del Valle\tUbeid\taubeid
Amin Ariel\tAparicio\taaparicio
Ana\tChoque\tachoque
Ana\tBoreya\taboreya
Ana Maria\tGranao\tagranao
Anahi Rosario\tCabello\tacabello
Analia\tValdez\tavaldez
Analia\tCorrado\tacorrado
Analia\tSaavedra\tnsaavedra
Analia\tLeañoz\taleanoz
Andrea\tMonasterio\tamonasterio
Andrea\tConde\taconde
Andrea\tOrellana\taorellana
Andrea\tRecchiuto\tarecchiuto
Andrea\tConde 2\taconde2
Andrea Silvana\tQuintos\taquintos
Angel\tCabezas\tacabezas
Angel Alberto\tChavez\tachavez
Angelina\tRobles\tarobles
Antonela Paola\tVaque Bazan\tavaquebazan
Arancibia\tSoledad\tsarancibia
Ariel\tAlonso\taalonso
Ariel\tGraneros\tarielgraneros
Arturo\tPereyra\tapereyra
Audiencia Civil\t\tsalacivil
Augusto\tDiaz\tadiaz
Aurelia Viviana\tBazan\tavbazan
Barbara\tDe las Cruces\tbdelascruces
Belen\tArtaza\tbartaza
Belen\tMayans\tbmayans
Belen\tMiranda\tbmiranda
Belen\tRios\tbrios
Belen\tFernandez Boga\tmfboga
Brenda Eliana\tGuiberguis\tbeguiberguis
Camara\t\tcamara
Camila\tCarabajal\tccarabajal
Carina\tPicardo\ticpicardo
Carlos\tBalvoa\tcbalvoa
Carlos\tSanhueza\tcsanhueza
Carlos Marcelo\tVillagran\tmvillagran
Carola Alexandra\tLopez Lucca\tcalopezlucca
Carolina\tCusi\tccusi
Cecilia\tMiranda Yapura\tcmiranda
Cecilia\tBrito\tcbrito
Cesar\tArias\tcarias
Cesar\tPistan\tcpistan
Cesar\tLages\tclages
Cesar Antonio\tCorrado\tccorrado
Cintya\tGomez Samman\tcgomez
Claudia\tGonzalez\tcgonzalez
Claudia\tMora\tCmora
Claudia\tPerez\tcperez
Claudia Emilia\tIbañez\tcibanez
Claudio\tRojas\tcrojas
Claudio\tRamos\tcramos
cloudsp\t\tcloudsp
Cristian\tDavila\tcdavila
Cristian\tGranados\tcgranados
Damian\tAlfaro\tdalfaro
Damian Victor\tGutierrez\tdgutierrez
Daniel\tQuiroz\tdquiroz
Daniel\tQuiros\tdquiros
Daniel\tCorrado\tdcorrado
Daniela\tBujad\tdbujad
Dante Oscar\tRivas\tdorivas
Dario\tYañez\tdyanez
Dario\tRotondo\tdrotondo
Diana Nahir\tBejarano\tDbejarano
Diego\tMasacessi\tdmasacessi
Diego Mariano\tIñigo\tdiñigo
Diegol Eduardo\tOvando Ruiz\tdovandoruiz
Eladio\tGuesalaga\teguesalaga
Elcia\tPerez\teperez
Eliana\tHermosilla\tehermosilla
Elio\tUrzagasti\teurzagasti
Emilce\tRios\terios
Ernesto\tAngel\teangel
Ernesto Daniel\tValdez\tevaldez
Estela\tPilili\tepilili
Estrella M\tAngel Cecila\temangel
Eugenio\tMoreno\temoreno
Eusebio\tBazan\tebazan
Fabiana\tTorrico\tftorrico
Fabiola\tTarifa\tftarifa
Fabricia\tSingh Melano\tfsingh
Facundo\tMedina\tfmedina
Facundo Francisco\tYapura Zamar\tfyapura
Fatima\tRios\tfrios
Fatima Andrea\tBejarano\tfbejarano
Federico\tPerez\tfperez
Federico\tSerra\tfserra
Federico Antonio\tSaavedra Carrizo\tfsaavedracarrizo
Fernanda\tArmella\tfarmella
Fernando Francisco\tAsmuzi\tfasmuzi
Fernando Samuel\tPerez\tfsperez
Flavia\tMora\tfmora
Florencia\tArtaza\tfartaza
Florencia\tBaiud\tfbaiud
Florencia\tAldana\tfaldana
Florencia\tMoya Siares\tfmoyasiares
Florencia\tZalloco\tfzalloco
Franco\tGiovannini\tfgiovannini
Franco Isaac\tAltamirano\tfaltamirano
Gabriel\tTerraza\tgterraza
Gabriel\tBoban\tgboban
Gabriela\tCisneros\tgcisneros
Gabriela\tArias\tgarias
Gabriela\tSajama\tgsajama
Gabriela\tPerez Rojas\tgperezrojas
Gaston\tOliva\tgoliva
Gladis\tGuzman\tgguzman
glpi\t\tglpi
Gonzalo\tMercado\tgmercado
Gonzalo\tIlan\tgilan
Graciela\tVera\tgvera
Graciela\tFalkonier\tgfalkonier
Graciela Alejandra\tSilva\tasilva
Griselda\tAsmuzi\tgasmuzi
Guadalupe Anahi\tEstrada\tgestrada
Guido\tFlores\tgflores
Guillermo\tOtero\tgotero
Guillermo\tOtero 2\tgotero2
Gustavo\tMurad\tgmurad
Gustavo\tToro\tgtoro
Gustavo Ezequiel\tBazan\tgbazan
Hector\tEspeche\thespeche
Hector Farid\tMurad\thfmurad
Hernan\tCasasola\thcasasola
Hernan\tTorres\thtorres
Horacio\tIñigo\thinigo
Horacio J.\tMacedo\thjmacedo
Hugo\tMansilla\thmansilla
Hugo\tAcosta\thacosta
Hugo Jose\tFalkonier\thfalkonier
Ines\tConde\ticonde
Invitado\t\togjinvitado
Invitado3\t\tinvitado3
invitados2\tinvi\tinvitados2
Ivan\tOliver\tioliver
Jacobo\tCarrizo\tjcarrizo
Jaqueline\tAraez\tjaraez
Javier\tBaiud\tjbaiud
Jimena\tÁngel Tapia\tjangel
Joaquin\tAvilez\tjavilez
Jorge\tSamman\tjsamman
Jorge\tPerez\tjperez
Jorge Edgardo\tToscano\tjetoscano
Jorgelina\tCanizares\tjcanizares
Jose\tZambrano\tjzambrano
Jose Leonel\tCarrizo\tjlcarrizo
Jose Luis\tVasile\tjvasile
Jose Luis\tTorres\tjtorres
Julia\tSpolita\tjspolita
Julio\tSallago\tjsallago
Justina\tVechetti\tjvechetti
Laura\tDuaso\tlduaso
Laura\tRodriguez\tlrodriguez
Laura Julieta\tZallocco\tlzallocco
Leandro Agustín\tRamos\tlramos
Leonardo\tWendel\tlwendel
Leonardo Ariel\tZazzal\tlzazzali
Liliana\tGarcia Legrand\tlgarcia
Liliana\tPellegrini\tlpellegrini
Liliana Beatriz\tArgote\tlargote
Lorena\tMansilla\tlmansilla
Lorena\tChuquimia\tlchuquimia
Lourdes Mariana\tPiccolomini\tlpiccolomini
Lucia Natalia\tMachaca\tlmachaca
Luciana\tMontilli\tlmontilli
Luis\tLewis\tllewis
Luis\tLewin\tllewin
Luis\tPerea\tlperea
Luz Maria\tMengual\tlmengual
Mabel\tSakal\tmsakal
Magdalena\tCarranza\tmcarranza
Malena\tVillena\tmvillena
Marcela\tCorrado\tmacorrado
Marcela\tSoria\tmsoria
Marcela\tFerrario\tmferrario
Marcelo\tTejerina\tmtejerina
Marcelo\tIbañez\tmibanez
Marcelo\tRodriguez\tmrodriguez
Marcelo\tJuarez Almaraz\tmalmaraz
Marcelo Alejandro\tAparicio\tmaaparicio
Maria Agustina\tChemes\tmchemes
Maria Elisa\tGuzman\tmguzman
Maria Graciela\tUbeid\tmubeid
Maria Jose\tAlcaraz\tmjalcaraz
Maria Leonor\tCabrera\tmcabrera
Maria Paula\tParucchi\tmparucchi
Maria Solana\tLopez Castro\tmslopezcastro
Mariana\tMora\tmmora
Mariana\tLara\tmlara
Mariana\tRoldan\tmroldan
Mariana\tChicarrico\tmchicarrico
Marianela\tTomas\tmtomas
Mariel\tMarquez\tmmarquez
Mariela\tArgañaraz\tmargañaraz
Mariela\tAleman\tmaleman
Mariela de los Angeles\tTejerina\tmatejerina
Mariela Ines\tMeyer\tmmeyer
Mario\tMoyano\tmmoyano
Mario\tVazquez\tmvazquez
Mario Aldo\tMoyano\tamoyano
Marisol\tFerreyra\tmferreyra
Marta Veronica\tSalas\tmsalas
Martia Teresa\tZuco\ttzuco
Martin\tCorrado\tmcorrado
Martin\tSosa\tmsosa
Matias\tNieto\tMnieto
Matias\tUrzagasti\tmurzagasti
Maximiliano\tAlvarez\tmalvarez
Maximiliano\tZalazar\tmazalazar
Maximiliano Federico\tQuinteros\tmquinteros
Melisa\tNavarro\tmnavarro
Micaela\tOrtega\tmortega
Miguel\tSaldaño\tmsaldano
Miguel\tRomero\tmromero
Miguel\tCespedes\tmcespedes
Miguel\tRuiz Cointte\tmruiz
Miguel Angel\tBravo\tmbravo
Milena\tElguero\tmelguero
Mirian\tZeballos\tmceballos
Mirta\tEljure\tmeljure
Mirta del Milagro\tVega\tmvega
Miryam\tAlvarado\tmalvarado
Misael Joel\tFernandez\tMfernandez
Monica\tFortunato\tmfortunato
Monica\tSanchez\tmsanchez
Monica\tCabello\tmcabello
Moriana\tAbraham\tmabraham
Nadia\tFalkonier\tnfalkonier
Nadia\tGonzalez\tnggonzalez
Nahir\tHarika\tnharika
Natalia\tSoletta\tnsoletta
Natalia\tSalas\tnsalas
Natalia\tZamar\tnzamar
Natalia Cecilia\tAyala\tnayala
Natalie\tSimone\tnsimone
Nelida\tGarcia\tngarcia
Nestor\tGonzalez\tngonzalez
nextcloudsis\t\tnextcloudsis
Nicolas\tHerrera\tnherrera
Nicolas\tCazon\tncazon
Nicolás\tNuttini\tnnuttini
Nicolas Federico\tSamman\tnsamman
Nidia Abigail\tBejarano\tnbejarano
Noelia\tChavez Rios\tnchavez
Noelia\tCasasola\tncasasola
Noelia del Rosario\tBarconte\tnbarconte
Nora\tBeltramo\tnbeltramo
Nora\tYapura\tnyapura
obsstudio\t\tobscontrol
Olga del Carmen\tSanchez de Bustamante\tosanchez
Olver\tLegal\tlolver
Operador\tCamara Civil Voc 10\tvocalia10
Operador\tCamara Civil Voc 11\tvocalia11
Operador\tCamara Civil Voc 12\tvocalia12
Oscar\tNuttini\tonuttini
Pablo\tRuiz\tpruiz
Pamela\tde las Cruces\tpdelascruces
Paola\tGuzman\tpguzman
Patricia\tIbañez\tpibanez
Patricia\tBaiud\tpbaiud
Patricia\tAleman\tpaleman
Patricia\tDiaz\tpdiaz
Patricia\tLescano\tplescano
Patricia\tGarnica\tpgarnica
Patricia del Valle\tPlanckensteiner\tpplanckensteiner
Paula\tZamar\tpzamar
Paula Solana\tBlanco\tpblanco
pruebavideo\tprueba\tpruebavideo
Rafael Ernesto\tYucra\tryucra
Raquel\tLezana\trlezana
Raul\tFernandez\trfernandez
Raul Ernesto\tBazan\trebazan
Rebeca\tTorres\trtorres
Reyna\tMachuca\trmachuca
Ricardo\tRoldan\trroldan
Rita Elizabeth\tSoria\trsoria
Roberto\tAlcoba\tralcoba
Rocio Natalia\tMonzon\trmonzon
rocketchat\t\trocketchat
Rodrigo\tBazan\trbazan
Rodrigo\tGomez\trgomez
Rogelio\tOrtuño\trortuño
Rolando\tVazquez\trvazquez
Rolando\tRojas\trrojas
Romina\tPerez\trperez
Roxana\tOrellana\trorellana
Ruben\tFerreyra\trferreyra
Ruben Omar\tYurquina\tryurquina
Ruth\tTintilay\trtintilay
Sandra\tGaspar\tsgaspar
Sandra\tPerez\tsperez
Sandra\tChiquello\tlchiquello
scriptcase\t\tscriptcase
Segio\tSoletta\tssoletta
Sergio\tOrtiz\tsortiz
Sergio Martin\tGonzalez\tsmgonzalez
Sergio Ricardo\tRodriguez\tsrodriguez
Silvia\tValdiviezo\tsvaldiviezo
Silvia\tYecora\tsyecora
Silvia\tGuzman\tsguzman
Silvia Ines\tDangelis\tsdangelis
Silvina\tAhumaran\tsahumaran
Silvina\tGomez\tsgomez
Silvio\tAvalos\tsavalos
Soledad\tCorrea Laspiur\tscorrea
Sonia\tAraez\tsaraez
Tatiana\tAguiar\ttaguiar
Teresa\tHormigo\tthormigo
Valentina\tGonzalez\tvgonzalez
Valeria\tBarcat\tvbarcat
Veronica\tCocha\tvcocha
Veronica\tGarnica\tvgarnica
Veronica\tGonzalez\tvmgonzalez
Victor\tPinasco\tvpinasco
Victor Antonio\tPerez\tvperez
Victoria\tOrellana\tvorellana
Vilma\tRomero\tvromero
Vilma Natalia\tVilca Guitian\tvnvilcaguitian
Viviana\tAbraham\tvabraham
Viviana\tScaro\tvscaro
Viviana Ines\tOntiveros\tvontiveros
Ximena\tGrau\txgrau
Yanina\tTorres\tytorres
Zalazar\tFernanda\tfzalazar
"""

def populate():
    conn = sqlite3.connect(DB_FILE)
    
    # Create table if not exists (username, real_name)
    conn.execute('CREATE TABLE IF NOT EXISTS ad_users (username TEXT PRIMARY KEY, real_name TEXT)')
    
    # Process data
    count = 0
    lines = RAW_DATA.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 3:
            given = parts[0].strip()
            surname = parts[1].strip()
            username = parts[2].strip()
            
            real_name = f"{given} {surname}".strip()
            
            if username:
                conn.execute('INSERT OR REPLACE INTO ad_users (username, real_name) VALUES (?, ?)', 
                             (username, real_name))
                count += 1
                
    conn.commit()
    conn.close()
    print(f"Imported/Updated {count} users.")

if __name__ == "__main__":
    populate()
