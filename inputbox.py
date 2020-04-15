import pygame, pygame.font, pygame.sysfont, pygame.event, pygame.draw, string
from pygame.locals import *

def get_key():
  while 1:
    event = pygame.event.poll()
    if event.type == KEYDOWN:
      return event.key
    else:
      pass

def display_box(screen, message):
  "Print a message in a box in the middle of the screen"
  fontobject = pygame.font.SysFont("Courier New",18)
  pygame.draw.rect(screen, (0,0,0),
                   ((screen.get_width() / 2) - 150,
                    (screen.get_height() / 2) + 100,
                    300,20), 0)
  pygame.draw.rect(screen, (255,255,255),
                   ((screen.get_width() / 2) - 152,
                    (screen.get_height() / 2) + 102,
                    304,24), 1)
  if len(message) != 0:
    screen.blit(fontobject.render(message, 1, (255,255,255)),
                ((screen.get_width() / 2) - 150, (screen.get_height() / 2) + 102))
  pygame.display.flip()

def display_faction_status(screen, status_list):
    bigfontobject = pygame.font.SysFont("Courier New", 56)
    mediumfontobject = pygame.font.SysFont("Courier New", 42)
    fontobject = pygame.font.SysFont("Courier New",24)
    vert = 200
    screen.blit(bigfontobject.render('Tides of Darkness - Alpha', 1, (255,255,255)),
                ((screen.get_width() / 2) - 375, (screen.get_height() / 2) - 425))
    screen.blit(mediumfontobject.render('By Alex Stevens & Jim Clarke', 1, (255,255,255)),
                ((screen.get_width() / 2) - 290, (screen.get_height() / 2) - 350))
    screen.blit(fontobject.render('Current factions:', 1, (255,255,255)),
                ((screen.get_width() / 2) - 150, (screen.get_height() / 2) - 250))
    for x in status_list:
        screen.blit(fontobject.render(x, 1, (255,255,255)),
                ((screen.get_width() / 2) - 150, (screen.get_height() / 2) - vert))
        vert -= 25
    screen.blit (fontobject.render('All Warcraft images/concepts property of Blizzard Entertainment', 1, (255,255,255)),
                ((screen.get_width() / 2) - 270, (screen.get_height() / 2) + 250))

def display_loading_status(screen, loading_message, count):
    fontobject = pygame.font.SysFont("Courier New",24)
    screen.blit(fontobject.render(loading_message, 1, (255,255,255)),
                ((screen.get_width() / 2) - 575, (screen.get_height() / 2 + count)))
    pygame.display.flip()

def display_quit_option(screen):
  fontobject = pygame.font.SysFont("Courier New",24)
  screen.blit (fontobject.render('Any incorrect password quits.', 1, (255,255,255)),
                ((screen.get_width() / 2) - 270, (screen.get_height() / 2) + 300))
  

def ask(screen, question):
  "ask(screen, question) -> answer"
  pygame.font.init()
  current_string = []
  display_box(screen, question + ": " + "".join(current_string))
  while 1:
    inkey = get_key()
    if inkey == K_BACKSPACE:
      current_string = current_string[0:-1]
    elif inkey == K_RETURN:
      break
    elif inkey == K_MINUS:
      current_string.append("_")
    elif inkey <= 127:
      current_string.append(chr(inkey))
    display_box(screen, question + ": " + "".join(current_string))
  return "".join(current_string)

def main():
  screen = pygame.display.set_mode((320,240))
  print(ask(screen, "Name") + " was entered")

if __name__ == '__main__': main()
