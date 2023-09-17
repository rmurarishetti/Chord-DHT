all: chord 

chord: chord.py
	cp chord.py chord
	chmod +x chord

clean:
	rm -rf chord
