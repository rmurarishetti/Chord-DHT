all: chord chord_protobuf

chord: chord.py
	cp chord.py chord
	chmod +x chord

chord_protobuf:
	protoc --python_out=. protobuf/chord.proto

clean:
	rm -rf protobuf/*.py chord
