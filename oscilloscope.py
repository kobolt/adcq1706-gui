#!/usr/bin/python
import serial
import pygame
import time



class Oscilloscope(object):
	def __init__(self, tty_dev='/dev/ttyUSB0', trig_level=2048):
		self._con = serial.Serial(tty_dev, 115200, timeout=2.0)
		self._settings = {
			1 : {'hsync' : 3, 'trig' : trig_level, 'rise' : 1},
			2 : {'hsync' : 3, 'trig' : trig_level, 'rise' : 1}}

	def get_samples(self, channel):
		hsync = str(self._settings[channel]['hsync'])
		trig  = str(self._settings[channel]['trig'])
		rise  = str(self._settings[channel]['rise'])

		self._con.write('ST' + hsync + str(channel) + trig + rise + 'E')
		data = self._con.read(4003)
		if len(data) != 4003:
			return None
		if not (data[0] == 'S') and (data[1] == 'M') and (data[4002] == 'E'):
			return None

		samples = list()
		for i in range(0, 2000):
			samples.append(int((ord(data[i*2+2]) & 0x7F) + (ord(data[i*2+3]) & 0x1F) * 128))
		return samples

	def increase_hsync(self, channel):
		if self._settings[channel]['hsync'] < 6:
			self._settings[channel]['hsync'] += 1

	def decrease_hsync(self, channel):
		if self._settings[channel]['hsync'] > 0:
			self._settings[channel]['hsync'] -= 1

	def get_hsync(self, channel):
		return self._settings[channel]['hsync']

	def toggle_trig_rise(self, channel):
		if self._settings[channel]['rise'] == 1:
			self._settings[channel]['rise'] = 0
		else:
			self._settings[channel]['rise'] = 1

	def increase_trig_level(self, channel):
		if self._settings[channel]['trig'] < 3968:
			self._settings[channel]['trig'] += 256

	def decrease_trig_level(self, channel):
		if self._settings[channel]['trig'] > 128:
			self._settings[channel]['trig'] -= 256

	def get_trig_level(self, channel):
		return self._settings[channel]['trig']



class GUI(object):
	def __init__(self, oscilloscope, scale=1):
		if scale not in [1,2,4]:
			raise Exception("Invalid scale")
		self._scale = scale
		self._osc = oscilloscope
		self._ch_active = {1 : True, 2 : True}
		pygame.init()
		pygame.display.set_caption("Oscilloscope")
		self._screen = pygame.display.set_mode((500 * scale, 512 * scale))
		self._font = pygame.font.Font(pygame.font.get_default_font(), 12 * scale)

	def _toggle_channel(self, channel):
		if self._ch_active[channel] == True:
			self._ch_active[channel] = False
		else:
			self._ch_active[channel] = True 

	def _draw_samples(self, samples, color):
		prev_y = None
		for sample_no, sample in enumerate(samples):
			y = (4096 - sample) / (8 / self._scale)
			x = sample_no / (4 / self._scale)
			if prev_y == None:
				prev_y = y
			pygame.draw.line(self._screen, color, (x, prev_y), (x, y))
			prev_y = y
	
	def _draw_volt_grid(self):
		for pos, volt in [(48,1.5), (715,1), (1381,0.5), (2048,0), (2715,-0.5), (3381,-1), (4048,-1.5)]:
			y = pos / (8 / self._scale)
			pygame.draw.line(self._screen, (128, 128, 128), (0, y), ((500 * self._scale), y))
			text = self._font.render(str(volt) + "V", True, (128, 128, 128))
			if text.get_height() > y:
				self._screen.blit(text, (0, y + (1 * self._scale)))
			else:
				self._screen.blit(text, (0, y - text.get_height() + (1 * self._scale)))

	def _draw_time_grid(self, channel, color):
		hsync = self._osc.get_hsync(channel)
		if hsync == 0:
			time = [0,5,10,15,20,25,30,35,40,45]
			unit = "us"
		elif hsync == 1:
			time = [0,10,20,30,40,50,60,70,80,90]
			unit = "us"
		elif hsync == 2:
			time = [0,50,100,150,200,250,300,350,400,450]
			unit = "us"
		elif hsync == 3:
			time = [0,100,200,300,400,500,600,700,800,900]
			unit = "us"
		elif hsync == 4:
			time = [0,1,2,3,4,5,6,7,8,9]
			unit = "ms"
		elif hsync == 5:
			time = [0,2,4,6,8,10,12,14,16,18]
			unit = "ms"
		elif hsync == 6:
			time = [0,10,20,30,40,50,60,70,80,90]
			unit = "ms"

		for index in range(0, 10):
			x = index * (50 * self._scale)
			if x > 0:
				pygame.draw.line(self._screen, (128, 128, 128), (x, 0), (x, (512 * self._scale)))
			text = self._font.render(str(time[index]) + unit, True, color)
			if channel == 1:
				self._screen.blit(text, (x + (1 * self._scale), 0))
			if channel == 2:
				self._screen.blit(text, (x + (1 * self._scale), (512 * self._scale) - text.get_height()))

	def _draw_trig_line(self, channel, color):
		y = (4096 - self._osc.get_trig_level(channel)) / (8 / self._scale)
		pygame.draw.line(self._screen, color, (0, y), ((500 * self._scale), y))

	def loop(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
						return
					elif event.key == pygame.K_s:
						pygame.image.save(self._screen, "oscilloscope.png")
						print "Screenshot saved to 'oscilloscope.png'."
					elif event.key == pygame.K_1:
						self._toggle_channel(1)
					elif event.key == pygame.K_2:
						self._toggle_channel(2)
					elif event.key == pygame.K_3:
						self._osc.increase_hsync(1)
					elif event.key == pygame.K_4:
						self._osc.decrease_hsync(1)
					elif event.key == pygame.K_5:
						self._osc.increase_hsync(2)
					elif event.key == pygame.K_6:
						self._osc.decrease_hsync(2)
					elif event.key == pygame.K_7:
						self._osc.toggle_trig_rise(1)
					elif event.key == pygame.K_8:
						self._osc.toggle_trig_rise(2)
					elif event.key == pygame.K_e:
						self._osc.increase_trig_level(1)
					elif event.key == pygame.K_r:
						self._osc.decrease_trig_level(1)
					elif event.key == pygame.K_t:
						self._osc.increase_trig_level(2)
					elif event.key == pygame.K_y:
						self._osc.decrease_trig_level(2)

			self._screen.fill((255,255,255))
			self._draw_volt_grid()

			if self._ch_active[1]:
				self._draw_time_grid(1, (255,128,128))
				self._draw_trig_line(1, (255,128,128))
				samples = self._osc.get_samples(1)
				self._draw_samples(samples, (255,0,0))

			if self._ch_active[2]:
				self._draw_time_grid(2, (128,128,255))
				self._draw_trig_line(2, (128,128,255))
				samples = self._osc.get_samples(2)
				self._draw_samples(samples, (0,0,255))

			if (not self._ch_active[1]) and (not self._ch_active[2]):
				time.sleep(0.1) # To avoid 100% CPU usage.

			pygame.display.flip()



if __name__ == "__main__":
	import sys
	import getopt

	def print_usage_and_exit():
		print "Usage: %s [options]" % (sys.argv[0])
		print "Options:"
		print "  -h         Display this help and exit."
		print "  -d DEV     Serial TTY DEV to use instead of /dev/ttyUSB0."
		print "  -s SCALE   Scale of GUI, value 1, 2 or 4."
		print " "
		sys.exit(1)

	def print_keys():
		print "Keys:"
		print "  1 = Toggle channel #1"
		print "  2 = Toggle channel #2"
		print "  3 = Increase time/div for channel #1"
		print "  4 = Decrease time/div for channel #1"
		print "  5 = Increase time/div for channel #2"
		print "  6 = Decrease time/div for channel #2"
		print "  7 = Toggle rise/fall trigging for channel #1"
		print "  8 = Toggle rise/fall trigging for channel #2"
		print "  E = Increase trig level for channel #1"
		print "  R = Decrease trig level for channel #1"
		print "  T = Increase trig level for channel #2"
		print "  Y = Decrease trig level for channel #2"
		print "  S = Screenshot"
		print "  Q = Quit"

	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd:s:")
	except getopt.GetoptError as err:
		print "Error:", str(err)
		print_usage_and_exit()

	tty_dev = None
	scale = None
	for o, a in opts:
		if o == '-h':
			print_usage_and_exit()
		elif o == '-d':
			tty_dev = a
		elif o == '-s':
			scale = int(a)

	if tty_dev:
		osc = Oscilloscope(tty_dev)
	else:
		osc = Oscilloscope()

	if scale:
		gui = GUI(osc, scale)
	else:
		gui = GUI(osc)

	print_keys()
	gui.loop()



