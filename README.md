
## Getting Started

1. Clone this repo: `git clone https://github.com/daanzu/kaldi-grammar-simple.git`
1. Change to directory: `cd kaldi-grammar-simple`
1. Install dragonfly with Kaldi backend and necessary dependencies: `pip install dragonfly2[kaldi]`
    * See the [dragonfly documentation](https://dragonfly2.readthedocs.io/en/latest/kaldi_engine.html#setup) for details on installation
1. Download a Kaldi speech model from [KaldiAG releases](https://github.com/daanzu/kaldi-active-grammar/releases) and unzip it
1. Run `python kaldi_module_loader_plus.py`

## Other Software Helpful With Voice

Note: Any software that adds keyboard shortcuts makes it much easier to control via voice commands.

* **[Vimium](https://www.google.com/search?q=vimium) extension for web browsers:** Great for doing many browser commands via keyboard, especially selecting and following links. Highly flexible/customizable.

* **[AceJump](https://www.google.com/search?q=AceJump)/[EasyMotion](https://www.google.com/search?q=EasyMotion) extensions for text editors:** Can effectively replace the mouse for most large text movement operations.
Different extensions vary slightly in their particulars, but most major extensible text editors have at least one option.

* **[TabNine](https://tabnine.com) autocompletion extension for text editors:** Alternately hilariously and scarily good completion suggestions. (Laugh while watching Skynet learn to program itself!) Can frequently complete entire lines, saving many keystrokes. Available for most text editors and programming languages, and works well for plain english text too.

* **[Fish shell](https://fishshell.com/):** Shell that is non-POSIX but has many big quality-of-life improvements, particularly its autocompletion engine, which is great for voice. Works not only on Linux, but also well enough on Windows in an MSYS2 environment, even if you only use normal Windows tools.

* **[fzf](https://github.com/junegunn/fzf) fuzzy finder for the command-line:** Handy for many tasks, especially integrated with your shell history to easily and quickly find any previous command. Type something once, why type it again?

* **Random articles**
    * [Avoiding the productivity mouse-traps](https://medium.com/productivity-freak/avoiding-productivity-mousetraps-177d80fa533b)
