#!/usr/bin/python

###################################################
#                                                 #
# MAC0422 - Sistemas Operacionais - 2015/02       #
# Caio Lopes Demario                              #
# NUSP 7991187                                    #
# Marcos Kazuya Yamazaki                          #
# NUSP 7577622                                    #
#                                                 #
###################################################

import sys, re, fileinput, time

memoriaVirtual = None
listaAcesso    = None
listaTermino   = None
listaMemFisica = None # FIFO e SCP

processos     = []
mapeamento    = []
memoriaFisica = []

espaco    = 1 # first/next/quick
substitui = 1 # nru/fifo/scp/lru
intervalo = 1

matrizLRU = []

#################################################################
#
#        Memoria VIRTUAL
#        
class Node:
	#inicializa um no de lista ligada
	def __init__(self, livre=None, pid=None, nome_processo=None, inicio=None, tamanho=None, prev=None ,prox=None):
		self.livre = livre
		self.pid = pid
		self.nome_processo = nome_processo
		self.inicio = inicio
		self.tamanho = tamanho

		self.prev = prev
		self.prox = prox

	def __str__(self):
		return str(self.nome_processo)

#################################################################
#
#        Lista Ligada dos processos ordenados  
#        em tempo de cada referencia a cada processo
#
class Acesso:
	def __init__(self, pid=None, pos=None, t=None, proxAcesso=None):
		self.pid = pid
		self.pos = pos
		self.t = t
		self.proxAcesso = proxAcesso

#################################################################
#
#        Lista Ligada dos processos ordenados  
#        em tempo de termino de cada processo
#
class Termino:
	def __init__(self, pid=None, tf=None, proxTermino=None):
		self.pid = pid
		self.tf  = tf
		self.proxTermino = proxTermino

#################################################################
#
#        Lista Ligada circulear da memoria Fisica, para 
#        ajudar nos algoritmos FIFO e SCP
#     
class MemFisica:
	def __init__(self, pageFrame=None, proxFisica=None):
		self.pageFrame = pageFrame
		self.proxFisica = proxFisica

#############################################################################################
def imprimeTela():
	global memoriaVirtual
	global memoriaFisica
	global mapeamento

	print "\nMemoria Virtual"
	print "+--------+-----+---------+"
	print "| pagina | pid | address |"
	print "+--------+-----+---------+"

	k = 0
	aux = memoriaVirtual
	while aux:
		pag = aux.tamanho/16
		for i in range(0, pag):
			print "|   " + str(k).zfill(3) + "  | " + str(aux.pid).zfill(3) + " |   " + str(mapeamento[k]).zfill(3) + "   |"
			k += 1
		aux = aux.prox

	print "+--------+-----+---------+"
	print "\nMemoria Fisica"
	print "+------------+-----+---+"
	print "| Page Frame | pid | R |"
	print "+------------+-----+---+"

	for i in range(0, len(memoriaFisica)):
		print "|     " + str(i).zfill(3) + "    | " + str(memoriaFisica[i][0]).zfill(3) + " | " + str(memoriaFisica[i][1]) + " |"
	print "+------------+-----+---+"

#############################################################################################
#
#     
#        
#   
def imprimeArquivo():
	global memoriaVirtual
	global memoriaFisica

	mem_virtual = open("/tmp/ep2.vir", "wb")
	mem_fisica  = open("/tmp/ep2.mem", "wb")

	arrayDecimal = []
	arrayBinario = []

	aux = memoriaVirtual
	while aux:
		pag = aux.tamanho/16
		for i in range(0, pag):
			for j in range(0, 16):
				arrayDecimal.append(int(aux.pid))
		aux = aux.prox
	arrayBinario = bytearray(arrayDecimal)
	mem_virtual.write(arrayBinario)

	arrayDecimal = []

	for i in range(0, len(memoriaFisica)):
		for j in range(0, 16):
			arrayDecimal.append(memoriaFisica[i][0])
	arrayBinario = bytearray(arrayDecimal)
	mem_fisica.write(arrayBinario)

	mem_virtual.close()
	mem_fisica.close()

#############################################################################################
#
#
#	
def carrega(file):
	global listaAcesso
	global listaTermino
	global memoriaVirtual
	
	global processos
	global mapeamento
	global memoriaFisica
	global matrizLRU

	listaAcesso    = None
	listaTermino   = None
	listaMemFisica = None # FIFO e SCP
	memoriaVirtual = None

	processos      = []
	mapeamento     = []
	memoriaFisica  = []
	matrizLRU = []

	#cria uma lista de processos baseada no arquivo de processos
	#salva os processos do arquivo na lista de processos
	for linha in open(file):
		processos.append(linha.replace("\n", ""))

	#salva o tamanho da memoria fisica e virtual na variavel memoria
	espacoMemoria = re.findall('[0-9]+', processos.pop(0))

	# inicializa os arrays mapeamento da memoria virtual para a fisica
	for i in range(0, int(espacoMemoria[0])/16):
		memoriaFisica.append([255])
		memoriaFisica[i].append(0)
		
		matrizLRU.append([])
		for j in range(0, int(espacoMemoria[0])/16):
			matrizLRU[i].append(0)
	
	for i in range(0, int(espacoMemoria[1])/16):
		mapeamento.append(255)

	#divide as posicoes e tempo dos processos em uma lista
	for i in range(0, len(processos)):
		processos[i] = processos[i].split(' ')

		if listaTermino is None: 
			listaTermino = Termino(i, int(processos[i][2]), None)
		else:
			aux = listaTermino
			# adiciona struct na primeira posicao, caso o t dele eh o menor
			if int(processos[i][2]) < aux.tf:
				listaTermino = Termino(i, int(processos[i][2]), listaTermino)
			else : # procura onde deve ser colocado ele
				while aux is not None:
					if aux.proxTermino is None: # se nao tem um proximo, com certeza sera adicionado depois dele
						aux.proxTermino = Termino(i, int(processos[i][2]), None)
						break
					elif int(processos[i][2]) >= aux.tf and int(processos[i][2]) < aux.proxTermino.tf :
						aux2 = aux.proxTermino
						aux.proxTermino = Termino(i, int(processos[i][2]), aux2)
						break
					aux = aux.proxTermino

	# processos[i][0] = t0
	# processos[i][1] = nome_processo
	# processos[i][2] = tf
	# processos[i][3] = tamanho em bytes
	
	# Aqui eh criada uma lista ligada ordenada por tempo de todos os acessos
	# a memoria realizados por todos os processos
	for i in range(0, len(processos)):
		j = 4
		while j < len(processos[i]):
			if listaAcesso is None: 
				listaAcesso = Acesso(i, int(processos[i][j]), int(processos[i][j+1]),None)
			else:
				aux = listaAcesso
				# adiciona struct na primeira posicao, caso o t dele eh o menor
				if int(processos[i][j+1]) < aux.t:
					listaAcesso = Acesso(i, int(processos[i][j]), int(processos[i][j+1]), listaAcesso)
				else : # procura onde deve ser colocado ele
					while aux is not None:
						if aux.proxAcesso is None: # se nao tem um proximo, com certeza sera adicionado depois dele
							aux.proxAcesso = Acesso(i, int(processos[i][j]), int(processos[i][j+1]), None)
							break
						elif int(processos[i][j+1]) >= aux.t and int(processos[i][j+1]) < aux.proxAcesso.t :
							aux2 = aux.proxAcesso
							aux.proxAcesso = Acesso(i, int(processos[i][j]), int(processos[i][j+1]), aux2)
							break
						aux = aux.proxAcesso	
			j += 2

	# cria a memoria vistual, que no inicio vale o tamanho total dela
	memoriaVirtual = Node(True, 255, None, 0, int(espacoMemoria[1]), None, None)

#################################################################
#
#
#
def removePageFrame(pid):
	global memoriaFisica
	global listaMemFisica
	global matrizLRU

	# remover da matriz => matrizLRU
	# memoriaFisica[] guarda o PID e R, para cada pegaFrame
	for i in range(0, len(memoriaFisica)):
		if memoriaFisica[i][0] == pid:
			for k in range(0, len(matrizLRU)):
				matrizLRU[i][k] = 0

	# remover da lista  => listaMemFisica
	for i in range(0, len(memoriaFisica)):
		if memoriaFisica[i][0] == pid:
			aux = listaMemFisica
			
			while int(aux.proxFisica.pageFrame) != i:
				aux = aux.proxFisica

			if aux == aux.proxFisica:
				listaMemFisica = None
			else:
				if aux.proxFisica == listaMemFisica:
					listaMemFisica = listaMemFisica.proxFisica
				aux.proxFisica = aux.proxFisica.proxFisica 

	# remover da matriz => memoriaFisica
	for i in range(0, len(memoriaFisica)):
		if memoriaFisica[i][0] == pid:
			memoriaFisica[i][0] = 255
			memoriaFisica[i][1] = 0

#################################################################
#
#
#
def removeProcessoMemVir(pid):
	global memoriaVirtual
	global mapeamento

	# Procurar processo na memoria virtual
	auxDel = memoriaVirtual
	while auxDel.pid != pid: 
		auxDel = auxDel.prox

	for i in range(auxDel.inicio/16, (auxDel.inicio + auxDel.tamanho)/16):
		mapeamento[i] = 255

	# CASO 1: nao possui prev, nao possui prox
	if (not auxDel.prev) and (not auxDel.prox):
		auxDel.livre = True
		auxDel.pid = 255
		auxDel.nome_processo = None

	# CASO 2: nao possui prev, e prox com processo
	elif (not auxDel.prev) and (not auxDel.prox.livre):
		auxDel.livre = True
		auxDel.pid = 255
		auxDel.nome_processo = None

	# CASO 3: nao possui prev, e prox livre
	elif (not auxDel.prev) and (auxDel.prox.livre):
		auxDel.prox.inicio = auxDel.inicio
		auxDel.prox.tamanho = int(auxDel.prox.tamanho) + int(auxDel.tamanho)

		memoriaVirtual = auxDel.prox
		memoriaVirtual.prev = None

	# CASO 4: prev com processo, e nao possui prox
	elif (not auxDel.prev.livre) and (not auxDel.prox):
		auxDel.livre = True
		auxDel.pid = 255
		auxDel.nome_processo = None

	# CASO 5: prev livre, nao possui prox
	elif (auxDel.prev.livre) and (not auxDel.prox):
		auxDel.prev.tamanho = int(auxDel.prev.tamanho) + int(auxDel.tamanho)
		auxDel.prev.prox = None  

	# CASO 6: prev com preocesso, prox com processos
	elif (not auxDel.prev.livre) and (not auxDel.prox.livre):
		auxDel.livre = True
		auxDel.pid = 255
		auxDel.nome_processo = None

	# CASO 7: prev livre, prox com processo
	elif (auxDel.prev.livre) and (not auxDel.prox.livre):
		auxDel.prev.tamanho = int(auxDel.prev.tamanho) + int(auxDel.tamanho)

		auxDel.prev.prox = auxDel.prox
		auxDel.prox.prev = auxDel.prev

	# CASO 8: prev com processo, prox livre
	elif (not auxDel.prev.livre) and (auxDel.prox.livre):
		auxDel.prox.tamanho = int(auxDel.prox.tamanho) + int(auxDel.tamanho)
		auxDel.prox.inicio = auxDel.inicio

		auxDel.prev.prox = auxDel.prox
		auxDel.prox.prev = auxDel.prev

	# CASO 9: prev livre, prox livre
	else:
		auxDel.prev.tamanho = int(auxDel.prev.tamanho) + int(auxDel.tamanho) + int(auxDel.prox.tamanho)

		auxDel.prev.prox = auxDel.prox.prox
		if auxDel.prox.prox:
			auxDel.prox.prox.prev = auxDel.prev

#################################################################
#
#
#
def executa():
	global listaAcesso
	global listaTermino
	global memoriaVirtual
	global processos
	global espaco
	global substitui
	global intervalo

	ponteiroNF       = memoriaVirtual
	tempoExecucao    = 0
	processosProntos = 0

	proxChegar = 0

	print "Estado Inicial das memorias"
	imprimeTela()
	imprimeArquivo()

	while(1): 
		#################################################################
		#
		#    Carrega os processos na memoria virtual
		#
		while((proxChegar < len(processos)) and (int(processos[proxChegar][0]) == int(tempoExecucao))):
			if espaco == 1:
				firstFit(proxChegar)
			elif espaco == 2:
				nextFit(proxChegar, ponteiroNF)
			else:
				quickFit(proxChegar)
			proxChegar += 1

			imprimeArquivo()	
		#
		#################################################################
		#
		#    Tira os processos da memoria virtual, 
		#    quando atinge o tf de cada processo!
		#
		while listaTermino and int(listaTermino.tf) == tempoExecucao:
			removeProcessoMemVir(listaTermino.pid)
			removePageFrame(listaTermino.pid)
			listaTermino = listaTermino.proxTermino
			
			imprimeArquivo()
		#
		#################################################################
		#
		#    Verifica o proximo acesso a memoria
		#
		while listaAcesso and int(listaAcesso.t) == tempoExecucao:
			auxAces = memoriaVirtual
			while auxAces.pid != listaAcesso.pid: 
				auxAces = auxAces.prox

			# mapeamento, acha em que pagina essa posicao de memoria esta
			pagina = int((auxAces.inicio + listaAcesso.pos)/16)

			# Verifica se essa pagina ja esta carregada na memoria fisica
			if mapeamento[pagina] != 255:
				memoriaFisica[mapeamento[pagina]][1] = 1
				alteraMatrizLRU(mapeamento[pagina]) # Esta passando o PAGE FRAME!

			# Se nao esta, tenta achar um quadro de pagina vazia para ela,
			# ou se nao der, ocorreu um page fault
			else: 
				firstFitMemoriaFisica(listaAcesso.pid, pagina)
				
			listaAcesso = listaAcesso.proxAcesso
			
			imprimeArquivo()
		#
		#################################################################

		if tempoExecucao%5 == 0:
			zeraBitR()

		if tempoExecucao%int(intervalo) == 0:
			print "\nTempo de execucao: " + str(tempoExecucao)
			imprimeTela()

		if not listaTermino: 
			break
		
		time.sleep(1)
		tempoExecucao += 1

#################################################################
#
#	Zera o bit R apos 5 segundos que 
#   cada processo foi referenciada
#
def zeraBitR():
	for i in range(0, len(memoriaFisica)):
		memoriaFisica[i][1] = 0

#################################################################
#
#
#
def firstFitMemoriaFisica(pid, pagina):
	global listaMemFisica
	global matrizLRU
	global memoriaFisica
	global mapeamento

	# procura um quadro de pagina livre
	for i in range(0, len(memoriaFisica)):
		if memoriaFisica[i][0] == 255:
			memoriaFisica[i][0] = pid # Processo que esta usando a memoria
			                          # nao difere das paginas, de cada processo
			memoriaFisica[i][1] = 1   # Esse e equivalente ao bit R
			mapeamento[pagina] = i

			alteraMatrizLRU(i) # Passa o page frame!
			
			#######################################################
			#
			#   Cria a lista, ou adiciona, as pageFrame em
			# ordem de referencias! Para ser usado no FIFO e SCP
			#
			if not listaMemFisica:
				listaMemFisica = MemFisica(i, None)
				listaMemFisica.proxFisica = listaMemFisica
			else:
				auxMF = MemFisica(i, listaMemFisica.proxFisica)
				listaMemFisica.proxFisica = auxMF
				listaMemFisica = auxMF
			#
			#
			#######################################################
			return

	# Se chegar ate aqui, 
	# eh por que deu PAGE FAULT!
	if substitui == 1:
		nru(pid, pagina)
	elif substitui == 2:
		fifo(pid, pagina)
	elif substitui == 3:
		scp(pid, pagina)
	else: 
		lru(pid, pagina)

#################################################################
#
#   Funcao que devolve o proximo numero que seja multiplo de 16
#
def mul16(num):
	if num%16 == 0:
		return num
	else:
		return num - num%16 + 16

#############################################################################
#
#     Algoritmos para alocacao dos processos na memoria virtual
#
#############################################################################
#
#
#
def firstFit(pid):
	global memoriaVirtual
	global processos

	# atribui auxMV, a lista ligada da memoria virtual
	auxMV = memoriaVirtual

	while auxMV:
		if not auxMV.livre or int(auxMV.tamanho) < mul16(int(processos[pid][3])):
			auxMV = auxMV.prox
		else:
			if auxMV.livre and int(auxMV.tamanho) >= mul16(int(processos[pid][3])):
				if int(auxMV.tamanho) == mul16(int(processos[pid][3])): # se o tamanho for igual, substitui apenas
					auxMV.livre = False
					auxMV.pid = pid
					auxMV.nome_processo = processos[pid][1]
				else: # cria um novo Node, caso o livre tenha espaco maior
					aux2 = Node(False, pid, processos[pid][1], auxMV.inicio, mul16(int(processos[pid][3])), auxMV.prev, auxMV)

	 				if aux2.prev: aux2.prev.prox = aux2
					if memoriaVirtual == auxMV: memoriaVirtual = aux2
	 				
					auxMV.prev = aux2
					auxMV.tamanho = int(auxMV.tamanho) - mul16(int(processos[pid][3]))
					auxMV.inicio = int(auxMV.inicio) + mul16(int(processos[pid][3]))
			break


#################################################################
def nextFit(pid, ponteiroNF):
	global memoriaVirtual
	global processos

	# atribui auxMV, a lista ligada da memoria virtual
	auxMV = ponteiroNF

	while 1:
		if not auxMV.livre or int(auxMV.tamanho) < mul16(int(processos[pid][3])):
			if not auxMV.prox: 
				auxMV = memoriaVirtual
			else: 
				auxMV = auxMV.prox
		else:
			if auxMV.livre and int(auxMV.tamanho) >= mul16(int(processos[pid][3])):
				if int(auxMV.tamanho) == mul16(int(processos[pid][3])): # se o tamanho for igual, substitui apenas
					auxMV.livre = False
					auxMV.nome_processo = processos[pid][1]
				else: # cria um novo Node, caso o livre tenha espaco maior
					aux2 = Node(False, pid, processos[pid][1], auxMV.inicio, mul16(int(processos[pid][3])), auxMV.prev, auxMV)

	 				if aux2.prev: aux2.prev.prox = aux2
					if memoriaVirtual == auxMV: memoriaVirtual = aux2

					auxMV.prev = aux2
					auxMV.tamanho = int(auxMV.tamanho) - mul16(int(processos[pid][3]))
					auxMV.inicio = int(auxMV.inicio) + mul16(int(processos[pid][3]))
			break

#################################################################
def quickFit():
	pass

#########################################################################################
#
#	AQUI COMECA OS ALGORITMOS DE TROCA DOS FRAMES DE PAGINA, quando ocorre PAGE FAULT     
#
#########################################################################################
#
#
#
def trocaPagina(pageFrame, pid, pagina):
	global memoriaFisica
	global mapeamento
	for i in range(0, len(mapeamento)):
		if mapeamento[i] == pageFrame:
			mapeamento[i] = 255
			break

	memoriaFisica[pageFrame][0] = pid # Processo que esta usando a memoria
	                                  # nao difere das paginas, de cada processo
	memoriaFisica[pageFrame][1] = 1   # Esse e equivalente ao bit R
	mapeamento[pagina] = pageFrame

#################################################################
#
#
#
def alteraMatrizLRU(pageFrame):
	global matrizLRU

	for i in range(0, len(matrizLRU)):
		matrizLRU[pageFrame][i] = 1
		matrizLRU[i][pageFrame] = 0

#################################################################
#
#    Not Rencetly Used Page
#    Verifica o bit R, se estiver 0, escolha esse quadro de 
#    pagina para sair, caso contrario, tenta achar alguma, 
#    se nao achar, tire o primeiro quadro mesmo
#
def nru(pid, pagina):
	global memoriaFisica
	global mapeamento

	# Procura o primeiro com o Bit R == 0
	# Se nao achar, tira o primeiro!
	for i in range(0, len(memoriaFisica)):
		if memoriaFisica[i][1] == 0:
			trocaPagina(i, pid, pagina)
			return

	# Se chegou ate aqui, tira o primeiro, pois todos tem bit R == 1
	trocaPagina(0, pid, pagina)

#################################################################
#
#     First-in, First out
#     Tira aquele que entrou menos recentemente
#
def fifo(pid, pagina):
	global memoriaFisica
	global listaMemFisica

	trocaPagina(listaMemFisica.proxFisica.pageFrame, pid, pagina)
	listaMemFisica = listaMemFisica.proxFisica 

#################################################################
#
#    Second Chance Page
#    FIFO melhorado
#
def scp(pid, pagina):
	global memoriaFisica
	global listaMemFisica

	#    Verifica o bit R do proximo a sair
	#  se ele for igual a 1, zeramos o bit e 
	#  verificamos o proximo dele.
	#    O loop saira assim que encontrar o primeiro
	#  page Frame com o bit R igual a 0
	#    E mesmo que todos no inicio tenha o bir R == 1 
	#  Uma hora, todos os bits serao zerados, e assim tiraremos o 
	#  primeiro que ja tinha sido encontrado
	while memoriaFisica[listaMemFisica.proxFisica.pageFrame][1] == 1:
		memoriaFisica[listaMemFisica.proxFisica.pageFrame][1] = 0
		listaMemFisica = listaMemFisica.proxFisica 

	trocaPagina(listaMemFisica.proxFisica.pageFrame, pid, pagina)
	listaMemFisica = listaMemFisica.proxFisica 

#################################################################
#
#	Least Recently Used
#
def lru(pid, pagina):
	global matrizLRU
	
	# veja a matriz, e procura aquela que tem o menor numeros de 1's na linha
	binario = []
	for i in range(0, len(matrizLRU)):
		# Converte cada linha da matrizLRU em um numero binario
		# para depois converter em um numero na base 10
		binario.append(int("".join(map(str, matrizLRU[i])), base = 2)) 
	# Acha o index do menor valor da lista

	proximoSair = binario.index(min(binario))

	trocaPagina(proximoSair, pid, pagina)
	alteraMatrizLRU(proximoSair)
	
####################################################################################################
#
#     MAIN
#

while 1:
	sys.stdout.write("[ep2]: ")
	line = sys.stdin.readline()

	if re.search('^carrega [a-z0-9.-_/]+' , line):
		line = re.sub(r'carrega ', '', line)
		line = re.sub(r'\n$', '', line)
		arquivo = line
	elif re.search('^espaco [1-3]' , line):
		line = re.sub(r'espaco ', '', line)
		espaco = int(line)
	elif re.search('^substitui [1-4]' , line):
		line = re.sub(r'substitui ', '', line)
		substitui = int(line)
	elif re.search('^executa [0-9]+' , line):
		line = re.sub(r'executa ', '', line)
		intervalo = int(line)
		carrega(arquivo)
		executa()
	elif re.search('^sai$' , line):
		break
	else: 
		print "Comando nao reconhecido!"

####################################################################################################
