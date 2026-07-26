CHAPTERS := 00-frontmatter 01-khokhwam-thi-an-phid 02-deal-thi-mai-mi-khrai-hen \
	03-phap-thi-hai-pai 04-thi-ma-thi-thae-jing 05-bug-nai-kan-riang-ladab-css \
	06-nangsue-thi-tong-rai-dai-jing 07-khrueang-mue-thi-ngok-jak-khwam-jampen \
	08-font-thi-mai-koei-thuk-tidtang 09-link-thi-du-muean-chai-dai 10-yai-baan \
	11-khuen-web-jing 12-muea-phuean-bok-wa-yuenyan-laeo 13-khamphut-thi-mai-chai-khong-rao \
	14-bot-rian-thi-yon-klap-ma-sam 15-wan-ngan-jing

.PHONY: pdf clean

pdf:
	rm -f /tmp/book-zwsp.md
	for f in $(CHAPTERS); do \
		if [ -f "$$f.md" ]; then \
			python3 thai-wordbreak.py "$$f.md" >> /tmp/book-zwsp.md; \
			echo "" >> /tmp/book-zwsp.md; \
		fi; \
	done
	pandoc /tmp/book-zwsp.md -o /tmp/book-typst-body.typ -t typst
	sed -i '' 's/#horizontalrule/#line(length: 100%)/g' /tmp/book-typst-body.typ 2>/dev/null || \
		sed -i 's/#horizontalrule/#line(length: 100%)/g' /tmp/book-typst-body.typ
	cat book.typ /tmp/book-typst-body.typ > /tmp/book-full.typ
	typst compile --font-path fonts /tmp/book-full.typ our-journey.pdf
	@echo "--- font gate ---"
	typst compile --font-path fonts /tmp/book-full.typ our-journey.pdf 2>&1 | grep -i "unknown font" \
		&& echo "FIX FONTS" || echo "fonts OK"

clean:
	rm -f our-journey.pdf /tmp/book-zwsp.md /tmp/book-typst-body.typ /tmp/book-full.typ
