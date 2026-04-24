[![avatar u/demosthenex](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_3.png)](https://www.reddit.com/user/demosthenex/)

I've looked it over, and I have to say I really don't like YAML. This also seems specific to managing items, where I use Org more to take detailed notes. My note contents are more important than the headline information.

It's still an interesting take on trying to use mostly plain text but integrate more reporting integration.

3

[![avatar u/github-alphapapa](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_6.png)](https://www.reddit.com/user/github-alphapapa/)

When I go to [https://smos.online/](https://smos.online/), the first thing I see is "Log In / Sign Up". How could that possibly replace Emacs and Org for me? One of the chief reasons to use Emacs and Org is that _they belong to me_. They reside on _my_ computer. The data resides on _my_ computer.

Now you seem to indicate that I can install your tool locally. But then, apparently, I either have to run it in a browser (i.e. inferior to the Emacs environment/platform), or there's a bespoke terminal UI (again, inferior to the Emacs/Org platform).

> Org-mode was also my only reason to use Emacs as a vim-er so I have since also stopped using Emacs.

That's fine, use whatever you like. But it sounds like you never understood what makes Emacs great in the first place. Consider, e.g. the hundreds of Org-related packages that are available to install with a single command. And to customize your tool I'd have to...use Haskell? And compile a new binary with the Haskell toolchain? Lisp, man! Lisp! Incremental development! Real-time definition and compilation!

I don't mean to denigrate your work. If you like Haskell, great. You scratched your own itch and took the time to share it, great. I'm with you.

But you seem to have completely missed the points of Emacs, Lisp, Org, and plain-text Org files.

In other words: [Emacs or Vi: The Definitive Answer](https://www.youtube.com/watch?v=V3QF1uAvbkU). ;)

By the way: while it may be allowed by the license, I feel like you shouldn't be using the Org logo in your project's logo. Let your project stand on its own and have its own.

4

I've been following smos github for a while, yet I haven't tried it. I wonder if you're gonna build a binary for Windows since I still have to use it at work and the lack of Wibdows binary is what kept me from trying it.

2

A native windows tool will not be possible with the current dependency setup. (brick does not work on windows, see [https://github.com/jtdaugherty/brick/issues/46](https://github.com/jtdaugherty/brick/issues/46))  
However, you can use smos from windows in the linux subsystem or in the browser.

2

[Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5s6rw3/?force-legacy-sct=1)

[![avatar u/yantar92](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_2.png)](https://www.reddit.com/user/yantar92/)

> Smos has replaced _my_ usage of org-mode because I was only using org-mode as a GTD organizing tool and never used any of the publishing aspects.

Could you explain why you decided to switch? Does smos provide some better functionality in comparison with org-mode?

2

\> Could you explain why you decided to switch?

Sure! I have never liked Emacs. I could rarely get it to start without runtime errors (a lot of which were entirely avoidable type errors). Smos is strongly statically typed and more robust (empirically) as a result.

Org-mode is plain-text based, which means it is future proof, but its syntax is not exactly machine-friendly. This made it difficult to write tooling for it. (This is a feature that I appreciated about Taskwarrior.)  
Smos is also future-proof in that respect, but it uses more machine readable formats under the hood (yaml or json) and doesn't expose this detail in the user interface.

Org-mode is hard to sync, or at least it was when I used it. You'd need something like org mode sync which added a bunch of ugly metadata into the file.  
You could also use dropbox but then you have to have a way to deal with the conflicts. Smos has distributed agreement using the syncing mechanism that does not put metadata into files anywhere. Syncing is straight-forward and safe. You can watch my talk about it if you'd like: [https://www.youtube.com/watch?v=MkbhHmAk47k](https://www.youtube.com/watch?v=MkbhHmAk47k)

\> Does smos provide some better functionality in comparison with org-mode?

Yes, that too. Smos is for self-management so it can make some handy assumptions about how to deal with files.

My favourite feature is that I can write \`smos-query work office\` and it will figure out how much time I have based on when my next meeting is, and show me only the tasks that I can do in that timeframe within the context of my office. So it won't show me "water plants at home", and if I only have 5 minutes until my next meeting then it will not show me "write X piece of code".

2

[![avatar u/yantar92](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_2.png)](https://www.reddit.com/user/yantar92/)

> Sure! I have never liked Emacs. I could rarely get it to start without runtime errors (a lot of which were entirely avoidable type errors).

That sounds like messed up config.

> Smos is strongly statically typed and more robust (empirically) as a result.

I conclude that you prefer statically typed programming languages. I assume that you are aware that both statically and dynamically typed languages have pros and cons.

> Org-mode is plain-text based, which means it is future proof, but its syntax is not exactly machine-friendly. This made it difficult to write tooling for it. (This is a feature that I appreciated about Taskwarrior.) Smos is also future-proof in that respect, but it uses more machine readable formats under the hood (yaml or json) and doesn't expose this detail in the user interface.

FYI. Org-mode syntax is fully representable in terms of Elisp s-exps. One may even store org files as s-exps. However, the main format is still plain text for opposite reasons - be able to read the files without access to Emacs and org-mode.

> Org-mode is hard to sync, or at least it was when I used it. You'd need something like org mode sync which added a bunch of ugly metadata into the file.

Could you elaborate? What kind of sync? What metadata?

> You could also use dropbox but then you have to have a way to deal with the conflicts. Smos has distributed agreement using the syncing mechanism that does not put metadata into files anywhere. Syncing is straight-forward and safe. You can watch my talk about it if you'd like: [https://www.youtube.com/watch?v=MkbhHmAk47k](https://www.youtube.com/watch?v=MkbhHmAk47k)

I have watched the talk. I am not professional programmer. For me, the scheme does not look too different from Git server-client protocol. Also, is there anything special about smos file format that makes it work with your `mergeful`, but not possible with plain text?

> My favourite feature is that I can write `smos-query work office` and it will figure out how much time I have based on when my next meeting is, and show me only the tasks that I can do in that timeframe within the context of my office. So it won't show me "water plants at home", and if I only have 5 minutes until my next meeting then it will not show me "write X piece of code".

If I understand correctly, it implies that you have effort estimates for all the TODOs. What about tasks without an estimate?

For the context, org-mode has tags, which can be used to mark the appropriate context. One can easily filter daily agenda (equivalent of `smos-query`) by specific tag (including context tag). (In my own workflow, I even made it mandatory to select the current context).

Effort estimates are also available in org-mode. One can also filter agenda by effort estimates not larger than certain time period. There is no automatic filtering based on the time left to next calendar event though.

> Smos is for self-management so it can make some handy assumptions about how to deal with files.

If you don't mind, could you provide more examples?

4

[Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5seow0/?force-legacy-sct=1) [Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5s9whl/?force-legacy-sct=1) [Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5s8yzt/?force-legacy-sct=1)

[![avatar u/BulkyLoad87](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_7.png)](https://www.reddit.com/user/BulkyLoad87/)

Looks like a great project! Thanks for your efforts and for bringing it here. I'm heavy org-mode and emacs user and while I absolutely love my setup and emacs ways of life, I am personally very interested in poking tools outside of emacs.

However, the project itself reminds me more taskwarrior then org-mode. Polished, minimal and somewhat opinionated about the "proper" workflow and really easy to use out of the box. As I understood the project itself is written mostly in Haskell, so there is little room for customization (comparing with live system of emacs). There is customization abilities through yaml configuration and Haskell configuration, but it looks limited at the moment. Extensibility is where org-mode really shines for me.

I have yet to try it on my machine, but a bunch of questions:

1.  There is a converter from org-mode to its internal yaml format, but it looks like it will ignore priorities and your clocks?
    
2.  I can't seem to find any interlinking abilities. I can't link things between files, is it correct?
    
3.  Web interface is just a TUI in web interface, is it correct? What I am supposed to do if I want to access my notes from a phone? Or capture things? May be some exporting\\importing?
    
4.  Also it's not clear (for me) which license have you used. I am always a bit suspicious about "open source" term. It is indeed open, but is it [free](https://www.gnu.org/philosophy/free-sw.en.html)?
    

2

\> There is customization abilities through yaml configuration and Haskell configuration, but it looks limited at the moment. Extensibility is where org-mode really shines for me.

I'm not sure what you mean by limited. You can add your own actions, bindings, reports, ... Would you please expand on what you'd want?

> There is a converter from org-mode to its internal yaml format, but it looks like it will ignore priorities and your clocks?

It will do its best given [https://hackage.haskell.org/package/orgmode-parse](https://hackage.haskell.org/package/orgmode-parse) (which I didn't write) but I think you're right, yes.

> I can't seem to find any interlinking abilities. I can't link things between files, is it correct?

That's right. Smos is a semantic editor. I cannot guarantee the semantic correctness of links (broken links) accross files, so I haven't built any linking yet.

> Web interface is just a TUI in web interface, is it correct? What I am supposed to do if I want to access my notes from a phone? Or capture things? May be some exporting\\importing?

For capturing I recommend [https://intray.eu](https://intray.eu/) Smos is not for capturing.

I haven't yet found a valid reason to have to \_edit\_ files from the phone, but reading can indeed have some use-cases. I only 'work' from a desktop computer so I haven't built any such access yet.

> Also it's not clear (for me) which license have you used. I am always a bit suspicious about "open source" term. It is indeed open, but is it free?

It's MIT licensed, make of that what you will :) [https://github.com/NorfairKing/smos/blob/master/smos/LICENSE](https://github.com/NorfairKing/smos/blob/master/smos/LICENSE)

2

[![avatar u/BulkyLoad87](https://www.redditstatic.com/avatars/defaults/v2/avatar_default_7.png)](https://www.reddit.com/user/BulkyLoad87/)

> I'm not sure what you mean by limited. You can add your own actions, bindings, reports, ... Would you please expand on what you'd want?

Well, I was trying to express my impression from the project rather then say I miss some particular feature. My usage of English can be clunky at times. What meant my "customization abilities" is extensibility of the system: writing your own functions, packages and generally hacking the system.

I admit, I have very limited knowledge of Haskell and its infrastructure, but let's say I want to redefine TodoState. I can't do this, right? There is no way of redefining types or functions.

Or let's say I want to execute some code every scheduling attempt. And for example disallow that and print a warning, if some constraints are not met.

> It will do its best given [https://hackage.haskell.org/package/orgmode-parse](https://hackage.haskell.org/package/orgmode-parse) (which I didn't write) but I think you're right, yes.

Given that the target format is yaml, it's not a big problem. After initial export I can do some manual work. In fact I probably can make a macro for reformatting clocks...

> It's MIT licensed, make of that what you will :) [https://github.com/NorfairKing/smos/blob/master/smos/LICENSE](https://github.com/NorfairKing/smos/blob/master/smos/LICENSE)

Ah, I see, thanks. I'm still getting used to new github interface.

> I haven't yet found a valid reason to have to \_edit\_ files from the phone, but reading can indeed have some use-cases. I only 'work' from a desktop computer so I haven't built any such access yet.

I have two use cases of files editing:

1.  Grocery lists (or any other check lists) I make them at computer, export along with everything else I want to export and then just use them at them shop. I have tried more specialized software, but didn't like that. It's really simple approach, like pen and paper.
    
2.  Clocking out of computer: field work, unplanned meetings and that's sort of stuff.
    

> That's right. Smos is a semantic editor. I cannot guarantee the semantic correctness of links (broken links) accross files, so I haven't built any linking **yet**.

But you planning to build?

2

[Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5t0ic1/?force-legacy-sct=1) [Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5swwg6/?force-legacy-sct=1) [Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5swagl/?force-legacy-sct=1)

Commentaire supprimé par un membre de l’équipe de modération

2

1

Commentaire supprimé par un membre de l’équipe de modération

3

[Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g62h858/?force-legacy-sct=1) [Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g622l8k/?force-legacy-sct=1) [Continuer ce fil](https://www.reddit.com/r/orgmode/comments/ivlczu/comment/g5ub6xr/?force-legacy-sct=1)