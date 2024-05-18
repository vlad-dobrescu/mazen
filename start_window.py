import arcade
import arcade.gui
import os

pressed_start = False
entered_port = None

class QuitButton(arcade.gui.UIFlatButton):
    def on_click(self, event: arcade.gui.UIOnClickEvent):
        arcade.exit()
        os._exit(0)

class CustomInputText(arcade.gui.UIInputText):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_color = arcade.color.BLACK
        self.bg_color = arcade.color.LIGHT_GRAY
        self.border_color = arcade.color.WHITE
        self.caret_color = arcade.color.BLACK
        self.selection_color = arcade.color.GRAY

    def on_draw(self):
        self.draw_rectangle_filled(self.center_x, self.center_y, self.width, self.height, self.bg_color)
        super().on_draw()

class MyWindow(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "UIFlatButton Example", resizable=True)
        
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        arcade.set_background_color(arcade.color.WHITE)

        self.v_box = arcade.gui.UIBoxLayout()

        # Add large text at the top
        instruction_label = arcade.gui.UILabel(
            text="Input a port number to be able to start",
            font_size=20,
            text_color=arcade.color.WHITE,
            align="center",
            size_hint=(None, None)
        )
        self.v_box.add(instruction_label.with_space_around(bottom=40))

        # Create the input box with custom styling
        self.port_input_box = CustomInputText(
            width=200,
            text="",
            placeholder="Enter port number"
        )
        self.v_box.add(self.port_input_box.with_space_around(bottom=20))

        # Create the start button
        self.start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.start_button.on_click = self.on_click_start
        self.start_button.disabled = True  # Initially disabled
        self.v_box.add(self.start_button.with_space_around(bottom=20))

        # Create the quit button
        quit_button = QuitButton(text="Quit", width=200)
        self.v_box.add(quit_button)

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

        self.port_input_box.on_change = self.on_port_change

    def on_port_change(self, event):
        try:
            port = int(self.port_input_box.text)
            if 1024 <= port <= 65535:  # Valid port range
                self.start_button.disabled = False
            else:
                self.start_button.disabled = True
        except ValueError:
            self.start_button.disabled = True

    def on_click_start(self, event):
        global pressed_start, entered_port
        pressed_start = True
        entered_port = int(self.port_input_box.text)
        arcade.close_window()

    def on_draw(self):
        self.clear()
        self.manager.draw()

def run_start_window():
    window = MyWindow()
    arcade.run()
