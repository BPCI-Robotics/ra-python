from vex import *
brain = Brain()

class SelectionMenu:
    class Option:
        def __init__(self, name: str, color: Color, choices: list[Any]):
            self.name = name
            self.color = color
            self.choices = choices
            self.index = 0
            self.length = len(choices)

        def value(self) -> Any:
            return self.choices[self.index]
        
        def next(self) -> None:
            self.index = (self.index + 1) % self.length

    def add_option(self, name: str, color: Color, choices: list[Any]):
        self.options.append(SelectionMenu.Option(name, color, choices))
        self.count += 1
    
    def __init__(self):
        self.count = 0
        self.options: list[SelectionMenu.Option] = []

        brain.screen.pressed(self.on_brain_screen_press)
    
    def on_brain_screen_press(self):
        x = brain.screen.x_position()
        y = brain.screen.y_position()

        if y < 240 - 30:
            return
        
        self.options[x // self.count].next()

        self.draw()
    
    def get_all(self):
        d = {}
        for option in self.options:
            d[option.name] = option.value()
        
        return d

    def draw(self):
        brain.screen.clear_screen(Color.BLACK)

        # Print the configurations
        brain.screen.set_font(FontType.MONO15)

        for i, option in enumerate(self.options):
            brain.screen.set_pen_color(option.color)
            brain.screen.set_cursor(i + 1, 1)
            brain.screen.print(option.name + ": " + option.value())
        
        # Draw the buttons
        # |--10--|Button|--10--|Button|--10--|Button|--10--|

        canvas_width = 480
        canvas_height = 240

        rect_width = (canvas_width - 10 * (self.count + 1)) / self.count
        rect_height = 30

        for i, option in enumerate(self.options):
            brain.screen.draw_rectangle(
                10 + (10 + rect_width) * i, 
                canvas_height - (rect_height + 5),
                rect_width,
                rect_height,
                option.color
            )  